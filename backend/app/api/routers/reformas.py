"""Obras e reformas nos apartamentos (NBR 16280).

O morador comunica a reforma antes de começar — o que vai fazer, o prazo,
a empresa e, se mexe em estrutura, paredes ou instalações, o responsável
técnico com a ART ou o RRT. O síndico aprova, com as condições do
regimento, ou recusa dizendo o motivo; pode prorrogar o prazo e cancelar
a obra irregular. A portaria vê as aprovadas que ainda estão no prazo:
passado o fim previsto, a obra não aparece mais para ela. Quem comunica é
quem responde pelo apartamento, more ou não nele — o dono reforma antes
de alugar.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.tempo import agora_utc, hoje_local
from app.models.condominio import Unidade
from app.models.enums import Papel, StatusReforma
from app.models.reforma import Reforma
from app.models.usuario import Usuario
from app.schemas.reforma import (
    PRAZO_MAXIMO_DIAS, AvaliacaoReforma, CancelamentoReforma, ProrrogacaoReforma,
    ReformaEntrada, ReformaSaida,
)
from app.services import registro
from app.services.destinatarios import avisar, moradores_da_unidade, sindicos

router = APIRouter(prefix="/reformas", tags=["Obras e reformas"])

# Tempo para o síndico avaliar antes de a obra começar.
ANTECEDENCIA_MINIMA_DIAS = 2
# Reformas de pé por apartamento: contra engano e contra pedido repetido.
LIMITE_ATIVAS = 3
ATIVAS = (StatusReforma.PENDENTE, StatusReforma.APROVADA)


def _hoje() -> date:
    return hoje_local()


def _periodo(r: Reforma) -> str:
    return f"de {r.inicio:%d/%m/%Y} a {r.fim:%d/%m/%Y}"


def _situacao(r: Reforma, hoje: date) -> str:
    if r.status == StatusReforma.PENDENTE:
        return "aguardando"
    if r.status == StatusReforma.APROVADA:
        if hoje < r.inicio:
            return "agendada"
        return "em_andamento" if hoje <= r.fim else "prazo_encerrado"
    return r.status.value


def _da_unidade(usuario: Usuario, r: Reforma) -> bool:
    """O morador vê as do apartamento comunicadas desde que está nele: o
    novo dono não vê a obra do anterior."""
    return (usuario.papel == Papel.MORADOR and r.unidade_id == usuario.unidade_id
            and r.criado_em >= usuario.unidade_desde)


def _saida(r: Reforma, usuario: Usuario, hoje: date) -> ReformaSaida:
    sindico = usuario.papel == Papel.SINDICO
    responde = sindico or _da_unidade(usuario, r)
    return ReformaSaida(
        id=r.id, unidade_id=r.unidade_id, unidade=r.unidade.identificacao,
        descricao=r.descricao, empresa=r.empresa, altera_estrutura=r.altera_estrutura,
        responsavel_tecnico=r.responsavel_tecnico, art_rrt=r.art_rrt,
        inicio=r.inicio, fim=r.fim, status=r.status, situacao=_situacao(r, hoje),
        solicitada_por_nome=r.solicitada_por.nome if r.solicitada_por else None,
        condicoes=r.condicoes, motivo_recusa=r.motivo_recusa,
        cancelada_pelo_sindico=bool(r.cancelada_por and r.cancelada_por.papel == Papel.SINDICO),
        motivo_cancelamento=r.motivo_cancelamento, concluida_em=r.concluida_em,
        criado_em=r.criado_em,
        pode_avaliar=sindico and r.status == StatusReforma.PENDENTE and r.fim >= hoje,
        pode_cancelar=responde and r.status in ATIVAS,
        pode_concluir=responde and r.status == StatusReforma.APROVADA and r.inicio <= hoje,
        pode_prorrogar=sindico and r.status == StatusReforma.APROVADA,
    )


def _consulta(condominio_id: int):
    return (
        select(Reforma)
        .options(selectinload(Reforma.unidade), selectinload(Reforma.solicitada_por),
                 selectinload(Reforma.cancelada_por))
        .where(Reforma.condominio_id == condominio_id)
    )


def _reforma_visivel(db: Session, usuario: Usuario, reforma_id: int) -> Reforma:
    """Travada até o commit: o síndico pode estar avaliando enquanto o
    morador cancela, e só um dos dois pode valer."""
    r = db.get(Reforma, reforma_id, with_for_update=True)
    if r is None or r.condominio_id != usuario.condominio_id or not (
            usuario.papel == Papel.SINDICO or _da_unidade(usuario, r)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Reforma não encontrada.")
    return r


@router.get("", response_model=list[ReformaSaida], summary="Obras e reformas")
def listar(
    status_: StatusReforma | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR, Papel.PORTEIRO)),
    db: Session = Depends(get_db),
) -> list[ReformaSaida]:
    """O morador vê as do apartamento; o síndico, todas; a portaria, as
    aprovadas que ainda estão no prazo — é o que ela precisa para deixar
    o material e os prestadores entrarem."""
    if usuario.condominio_id is None:
        return []
    hoje = _hoje()
    consulta = _consulta(usuario.condominio_id)
    if usuario.papel == Papel.PORTEIRO:
        consulta = consulta.where(Reforma.status == StatusReforma.APROVADA, Reforma.fim >= hoje)
        ordem = (Reforma.inicio, Reforma.id)
    else:
        if usuario.papel == Papel.MORADOR:
            consulta = consulta.where(and_(Reforma.unidade_id == usuario.unidade_id,
                                           Reforma.criado_em >= usuario.unidade_desde))
        if status_ is not None:
            consulta = consulta.where(Reforma.status == status_)
        ordem = (Reforma.inicio.desc(), Reforma.id.desc())
    return [_saida(r, usuario, hoje)
            for r in db.scalars(consulta.order_by(*ordem).limit(300)).all()]


@router.post("", response_model=ReformaSaida, status_code=status.HTTP_201_CREATED,
             summary="Comunicar a reforma")
def comunicar(
    dados: ReformaEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> ReformaSaida:
    unidade = db.get(Unidade, morador.unidade_id) if morador.unidade_id else None
    if unidade is None or unidade.condominio_id != morador.condominio_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Seu cadastro não está ligado a um apartamento.")
    hoje = _hoje()
    if dados.inicio < hoje + timedelta(days=ANTECEDENCIA_MINIMA_DIAS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Comunique a reforma com pelo menos {ANTECEDENCIA_MINIMA_DIAS} dias de "
                   "antecedência, para o síndico avaliar antes de a obra começar.")

    # Dois pedidos do mesmo apartamento ao mesmo tempo esperam um pelo
    # outro; sem isso, os dois passariam pelo limite juntos.
    db.execute(select(func.pg_advisory_xact_lock(
        morador.condominio_id, func.hashtext(f"reforma:{unidade.id}"))))
    ativas = db.scalar(
        select(func.count()).select_from(Reforma)
        .where(Reforma.unidade_id == unidade.id, Reforma.status.in_(ATIVAS),
               Reforma.fim >= hoje)
    )
    if ativas >= LIMITE_ATIVAS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O apartamento já tem {ativas} reformas comunicadas, o limite. Conclua "
                   "ou cancele uma antes de comunicar outra.")

    r = Reforma(condominio_id=morador.condominio_id, unidade_id=unidade.id,
                solicitada_por_id=morador.id, status=StatusReforma.PENDENTE,
                **dados.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    tecnico = (f" Mexe em estrutura ou instalações; responsável técnico: "
               f"{r.responsavel_tecnico} (ART/RRT {r.art_rrt})." if r.altera_estrutura else "")
    avisar(sindicos(db, r.condominio_id), "Reforma para avaliar",
           f"O apartamento {unidade.identificacao} comunicou uma reforma {_periodo(r)}: "
           f"{r.descricao}.{tecnico} Aprove ou recuse pelo SmartCondo.")
    return _saida(r, morador, hoje)


@router.post("/{reforma_id}/avaliacao", response_model=ReformaSaida,
             summary="Aprovar ou recusar a reforma")
def avaliar(
    reforma_id: int,
    dados: AvaliacaoReforma,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> ReformaSaida:
    r = _reforma_visivel(db, sindico, reforma_id)
    hoje = _hoje()
    if r.status != StatusReforma.PENDENTE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta reforma já foi avaliada ou cancelada.")
    if dados.aprovada and r.fim < hoje:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="O prazo desta reforma já passou. Ela só pode ser recusada.")
    r.status = StatusReforma.APROVADA if dados.aprovada else StatusReforma.RECUSADA
    r.condicoes = dados.condicoes if dados.aprovada else None
    r.motivo_recusa = None if dados.aprovada else dados.motivo
    r.avaliada_por_id = sindico.id
    r.avaliada_em = agora_utc()
    if dados.aprovada:
        registro.registrar(db, sindico, registro.APROVOU, registro.REFORMA, r.id,
                           f"Condições: {r.condicoes}" if r.condicoes else None)
    else:
        registro.registrar(db, sindico, registro.RECUSOU, registro.REFORMA, r.id, r.motivo_recusa)
    db.commit()
    db.refresh(r)
    quem = moradores_da_unidade(db, r.unidade_id, so_quem_mora=False)
    if dados.aprovada:
        avisar(quem, "Reforma aprovada",
               f"A reforma do apartamento {r.unidade.identificacao} {_periodo(r)} foi aprovada"
               + (f". Condições: {r.condicoes}" if r.condicoes else "")
               + ". A portaria já está avisada; autorize a entrada dos prestadores em "
               "Visitantes Autorizados.")
    else:
        avisar(quem, "Reforma recusada",
               f"A reforma do apartamento {r.unidade.identificacao} {_periodo(r)} foi recusada "
               f"pelo síndico. Motivo: {r.motivo_recusa}")
    return _saida(r, sindico, hoje)


@router.post("/{reforma_id}/prorrogacao", response_model=ReformaSaida,
             summary="Prorrogar o prazo da reforma")
def prorrogar(
    reforma_id: int,
    dados: ProrrogacaoReforma,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> ReformaSaida:
    r = _reforma_visivel(db, sindico, reforma_id)
    hoje = _hoje()
    if r.status != StatusReforma.APROVADA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Só a reforma aprovada, ainda não concluída, é prorrogada.")
    if dados.fim <= r.fim or dados.fim < hoje:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O novo fim precisa ser depois do atual e de hoje.")
    if (dados.fim - r.inicio).days > PRAZO_MAXIMO_DIAS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="A reforma pode durar até um ano desde o início.")
    antes = r.fim
    r.fim = dados.fim
    registro.registrar(db, sindico, registro.EDITOU, registro.REFORMA, r.id,
                       f"Prazo prorrogado de {antes:%d/%m/%Y} para {r.fim:%d/%m/%Y}"
                       + (f": {dados.motivo}" if dados.motivo else ""))
    db.commit()
    db.refresh(r)
    avisar(moradores_da_unidade(db, r.unidade_id, so_quem_mora=False), "Reforma prorrogada",
           f"O prazo da reforma do apartamento {r.unidade.identificacao} foi prorrogado até "
           f"{r.fim:%d/%m/%Y}." + (f" {dados.motivo}" if dados.motivo else ""))
    return _saida(r, sindico, hoje)


@router.post("/{reforma_id}/conclusao", response_model=ReformaSaida,
             summary="Avisar que a reforma terminou")
def concluir(
    reforma_id: int,
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> ReformaSaida:
    r = _reforma_visivel(db, usuario, reforma_id)
    hoje = _hoje()
    if r.status != StatusReforma.APROVADA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Só a reforma aprovada pode ser concluída.")
    if r.inicio > hoje:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A reforma ainda não começou.")
    r.status = StatusReforma.CONCLUIDA
    r.concluida_em = agora_utc()
    if usuario.papel == Papel.SINDICO:
        registro.registrar(db, usuario, registro.EDITOU, registro.REFORMA, r.id,
                           "Reforma concluída")
    db.commit()
    db.refresh(r)
    if usuario.papel == Papel.MORADOR:
        avisar(sindicos(db, r.condominio_id), "Reforma concluída",
               f"O apartamento {r.unidade.identificacao} avisou que a reforma {_periodo(r)} "
               "terminou.")
    return _saida(r, usuario, hoje)


@router.post("/{reforma_id}/cancelamento", response_model=ReformaSaida,
             summary="Cancelar a reforma")
def cancelar(
    reforma_id: int,
    dados: CancelamentoReforma | None = None,
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> ReformaSaida:
    """O morador desiste; o síndico embarga a obra irregular (sem a ART,
    fora do que foi aprovado) — com o motivo, que vai para o apartamento."""
    r = _reforma_visivel(db, usuario, reforma_id)
    hoje = _hoje()
    if r.status not in ATIVAS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta reforma não está mais de pé.")
    motivo = dados.motivo if dados else None
    pelo_sindico = usuario.papel == Papel.SINDICO
    if pelo_sindico and not (motivo and len(motivo) >= 3):
        raise HTTPException(status_code=422,
                            detail="Informe o motivo do cancelamento; o apartamento recebe.")
    estava_aprovada = r.status == StatusReforma.APROVADA
    r.status = StatusReforma.CANCELADA
    r.cancelada_por_id = usuario.id
    r.cancelada_em = agora_utc()
    r.motivo_cancelamento = motivo
    if pelo_sindico:
        registro.registrar(db, usuario, registro.CANCELOU, registro.REFORMA, r.id, motivo)
    db.commit()
    db.refresh(r)
    if pelo_sindico:
        avisar(moradores_da_unidade(db, r.unidade_id, so_quem_mora=False), "Reforma cancelada",
               f"A reforma do apartamento {r.unidade.identificacao} {_periodo(r)} foi cancelada "
               f"pelo síndico. Motivo: {motivo}")
    elif estava_aprovada:
        avisar(sindicos(db, r.condominio_id), "Reforma cancelada",
               f"O apartamento {r.unidade.identificacao} cancelou a reforma aprovada "
               f"{_periodo(r)}.")
    return _saida(r, usuario, hoje)
