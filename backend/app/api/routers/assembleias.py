"""Assembleia virtual: o síndico convoca, cada apartamento vota uma vez.

Código Civil:
  - art. 1.354-A (Lei 14.309/2022): a assembleia pode ser eletrônica;
  - art. 1.354: todos os condôminos são convocados — aqui, por aviso;
  - art. 1.335, III: vota o condômino quite — apartamento com cobrança
    vencida não vota;
  - art. 1.352: as deliberações são por maioria; um voto por apartamento,
    dado pelo proprietário (more ou não no apartamento) ou, se nenhum
    proprietário tem cadastro, pelo inquilino;
  - arts. 1.341 e 1.351: algumas matérias pedem 2/3 dos condôminos, e
    aí contam todas as unidades, não só as que votaram.

Durante a votação ninguém vê o placar, nem o síndico: só quantos
apartamentos já votaram. A portaria não participa.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.tempo import agora_local, hoje_local
from app.models.assembleia import Assembleia, ItemPauta, Voto
from app.models.condominio import Unidade
from app.models.enums import (
    CanalVerificacao, EscolhaVoto, MaioriaExigida, Papel, StatusCobranca, StatusUsuario,
    TipoOcupacao,
)
from app.models.financeiro import Cobranca
from app.models.usuario import Usuario
from app.schemas.assembleia import (
    AssembleiaEntrada, AssembleiaSaida, CancelamentoAssembleia, CedulaEntrada,
    ItemPautaSaida, ResultadoItem,
)
from app.services import notificacao, registro

router = APIRouter(prefix="/assembleias", tags=["Assembleias"])

AGENDADA, ABERTA, ENCERRADA, CANCELADA = "agendada", "aberta", "encerrada", "cancelada"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _situacao(a: Assembleia, agora: datetime) -> str:
    if a.inativo:
        return CANCELADA
    if agora < a.abre_em:
        return AGENDADA
    if agora < a.encerra_em:
        return ABERTA
    return ENCERRADA


def _quando(momento: datetime) -> str:
    """"20/10 às 19h00", no fuso do condomínio."""
    return momento.astimezone(agora_local().tzinfo).strftime("%d/%m às %Hh%M")


def _total_unidades(db: Session, condominio_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Unidade).where(
        Unidade.condominio_id == condominio_id, Unidade.pendente.is_(False))) or 0


def _aprovado(maioria: MaioriaExigida, a_favor: int, contra: int, total: int) -> bool:
    if maioria == MaioriaExigida.DOIS_TERCOS:
        return total > 0 and a_favor * 3 >= total * 2
    if maioria == MaioriaExigida.UNANIMIDADE:
        return total > 0 and a_favor == total
    # Maioria simples dos votos; abstenção não conta, e empate não aprova.
    return a_favor > contra


def _motivo_sem_voto(db: Session, morador: Usuario) -> str | None:
    """Por que este morador não pode votar pelo apartamento (None: pode)."""
    if morador.unidade_id is None:
        return "Seu cadastro não está ligado a um apartamento."
    if morador.tipo_ocupacao != TipoOcupacao.PROPRIETARIO:
        proprietario = db.scalar(select(Usuario.id).where(
            Usuario.unidade_id == morador.unidade_id, Usuario.papel == Papel.MORADOR,
            Usuario.status == StatusUsuario.ATIVO,
            Usuario.tipo_ocupacao == TipoOcupacao.PROPRIETARIO,
        ).limit(1))
        if proprietario is not None or morador.tipo_ocupacao != TipoOcupacao.INQUILINO:
            return ("Quem vota pelo apartamento é o proprietário — ou, se nenhum tem "
                    "cadastro, o inquilino.")
    em_atraso = db.scalar(select(Cobranca.id).where(
        Cobranca.unidade_id == morador.unidade_id,
        Cobranca.status.in_((StatusCobranca.ABERTA, StatusCobranca.VENCIDA)),
        Cobranca.vencimento < hoje_local(),
    ).limit(1))
    if em_atraso is not None:
        return ("O apartamento tem cobrança vencida: pelo Código Civil (art. 1.335, III), "
                "só vota quem está quite.")
    return None


def _saida(db: Session, a: Assembleia, usuario: Usuario, agora: datetime) -> AssembleiaSaida:
    situacao = _situacao(a, agora)
    total = _total_unidades(db, a.condominio_id)
    ids = [i.id for i in a.itens]
    contagem: dict[int, dict[EscolhaVoto, int]] = {i: {} for i in ids}
    unidades_que_votaram = 0
    if ids:
        for item_id, escolha, n in db.execute(
            select(Voto.item_id, Voto.escolha, func.count())
            .where(Voto.item_id.in_(ids)).group_by(Voto.item_id, Voto.escolha)
        ).all():
            contagem[item_id][escolha] = n
        unidades_que_votaram = db.scalar(
            select(func.count(func.distinct(Voto.unidade_id))).where(Voto.item_id.in_(ids))
        ) or 0

    meus: dict[int, EscolhaVoto] = {}
    eh_morador = usuario.papel == Papel.MORADOR
    if eh_morador and usuario.unidade_id is not None and ids:
        meus = dict(db.execute(select(Voto.item_id, Voto.escolha).where(
            Voto.item_id.in_(ids), Voto.unidade_id == usuario.unidade_id)).all())

    itens = []
    for item in a.itens:
        resultado = None
        if situacao == ENCERRADA:
            votos = contagem[item.id]
            a_favor = votos.get(EscolhaVoto.A_FAVOR, 0)
            contra = votos.get(EscolhaVoto.CONTRA, 0)
            resultado = ResultadoItem(
                a_favor=a_favor, contra=contra, abstencao=votos.get(EscolhaVoto.ABSTENCAO, 0),
                aprovado=_aprovado(item.maioria, a_favor, contra, total),
            )
        itens.append(ItemPautaSaida(
            id=item.id, ordem=item.ordem, titulo=item.titulo, descricao=item.descricao,
            maioria=item.maioria, resultado=resultado, meu_voto=meus.get(item.id),
        ))

    saida = AssembleiaSaida(
        id=a.id, titulo=a.titulo, descricao=a.descricao, abre_em=a.abre_em,
        encerra_em=a.encerra_em, situacao=situacao,
        convocada_por_nome=a.convocada_por.nome if a.convocada_por else None,
        motivo_cancelamento=a.motivo_cancelamento, itens=itens, total_unidades=total,
        unidades_que_votaram=unidades_que_votaram, criado_em=a.criado_em,
    )
    if eh_morador:
        votou = bool(meus)
        motivo = "Seu apartamento já votou." if votou else _motivo_sem_voto(db, usuario)
        saida = saida.model_copy(update={
            "meu_apartamento_votou": votou,
            "posso_votar": situacao == ABERTA and motivo is None,
            "motivo_sem_voto": motivo,
        })
    return saida


def _da_assembleia(db: Session, usuario: Usuario, assembleia_id: int,
                   travar: bool = False) -> Assembleia:
    a = db.get(Assembleia, assembleia_id, with_for_update=travar)
    if a is None or a.condominio_id != usuario.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Assembleia não encontrada.")
    return a


def _avisar_moradores(db: Session, condominio_id: int, titulo: str, mensagem: str) -> None:
    for morador in db.scalars(select(Usuario).where(
        Usuario.condominio_id == condominio_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
    )).all():
        notificacao.notificar(morador.email, CanalVerificacao.EMAIL, titulo, mensagem)


@router.post("", response_model=AssembleiaSaida, status_code=status.HTTP_201_CREATED,
             summary="Convoca uma assembleia virtual")
def convocar(
    dados: AssembleiaEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> AssembleiaSaida:
    a = Assembleia(
        condominio_id=sindico.condominio_id, convocada_por_id=sindico.id,
        titulo=dados.titulo, descricao=dados.descricao,
        abre_em=dados.abre_em, encerra_em=dados.encerra_em,
        itens=[ItemPauta(ordem=n, titulo=i.titulo, descricao=i.descricao, maioria=i.maioria)
               for n, i in enumerate(dados.itens, start=1)],
    )
    db.add(a)
    db.flush()
    registro.registrar(db, sindico, registro.CRIOU, registro.ASSEMBLEIA, a.id)
    db.commit()
    db.refresh(a)

    # Art. 1.354: todos os condôminos precisam ser convocados.
    _avisar_moradores(
        db, a.condominio_id, "Assembleia convocada",
        f"{a.titulo}: votação pelo SmartCondo, de "
        f"{_quando(a.abre_em)} a {_quando(a.encerra_em)}. Pauta com "
        f"{len(a.itens)} {'item' if len(a.itens) == 1 else 'itens'}.",
    )
    return _saida(db, a, sindico, _agora())


@router.get("", response_model=list[AssembleiaSaida], summary="Lista as assembleias")
def listar(
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> list[AssembleiaSaida]:
    assembleias = db.scalars(
        select(Assembleia)
        .options(selectinload(Assembleia.itens), selectinload(Assembleia.convocada_por))
        .where(Assembleia.condominio_id == usuario.condominio_id)
        .order_by(Assembleia.abre_em.desc())
    ).all()
    agora = _agora()
    return [_saida(db, a, usuario, agora) for a in assembleias]


@router.get("/{assembleia_id}", response_model=AssembleiaSaida, summary="Uma assembleia")
def detalhar(
    assembleia_id: int,
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> AssembleiaSaida:
    return _saida(db, _da_assembleia(db, usuario, assembleia_id), usuario, _agora())


@router.post("/{assembleia_id}/votos", response_model=AssembleiaSaida,
             status_code=status.HTTP_201_CREATED,
             summary="O apartamento vota em todos os itens da pauta")
def votar(
    assembleia_id: int,
    dados: CedulaEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> AssembleiaSaida:
    a = _da_assembleia(db, morador, assembleia_id)
    agora = _agora()
    situacao = _situacao(a, agora)
    if situacao != ABERTA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            AGENDADA: "A votação ainda não abriu.",
            ENCERRADA: "A votação já foi encerrada.",
            CANCELADA: "Esta assembleia foi cancelada.",
        }[situacao])
    motivo = _motivo_sem_voto(db, morador)
    if motivo is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=motivo)

    # Cédula completa: um voto em cada item, nem mais nem menos.
    ids = {i.id for i in a.itens}
    votados = [v.item_id for v in dados.votos]
    if sorted(votados) != sorted(ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Vote uma vez em cada item da pauta.")

    # Trava o apartamento: dois moradores votando ao mesmo tempo não passam
    # juntos pela conferência; a restrição do banco é a última garantia.
    db.get(Unidade, morador.unidade_id, with_for_update=True)
    if db.scalar(select(Voto.id).where(Voto.item_id.in_(ids),
                                       Voto.unidade_id == morador.unidade_id).limit(1)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seu apartamento já votou nesta assembleia.")
    for voto in dados.votos:
        db.add(Voto(item_id=voto.item_id, unidade_id=morador.unidade_id,
                    usuario_id=morador.id, escolha=voto.escolha, votado_em=agora))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seu apartamento já votou nesta assembleia.") from None
    return _saida(db, a, morador, agora)


@router.post("/{assembleia_id}/cancelamento", response_model=AssembleiaSaida,
             summary="Cancela uma assembleia, com o motivo")
def cancelar(
    assembleia_id: int,
    dados: CancelamentoAssembleia,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> AssembleiaSaida:
    a = _da_assembleia(db, sindico, assembleia_id, travar=True)
    agora = _agora()
    if _situacao(a, agora) in (ENCERRADA, CANCELADA):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A assembleia já foi encerrada ou cancelada.")
    a.inativo_em = agora
    a.inativado_por_id = sindico.id
    a.motivo_cancelamento = dados.motivo
    registro.registrar(db, sindico, registro.CANCELOU, registro.ASSEMBLEIA, a.id, dados.motivo)
    db.commit()
    db.refresh(a)
    _avisar_moradores(db, a.condominio_id, "Assembleia cancelada",
                      f"{a.titulo} foi cancelada pelo síndico. Motivo: {dados.motivo}")
    return _saida(db, a, sindico, agora)
