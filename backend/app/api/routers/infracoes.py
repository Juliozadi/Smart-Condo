"""Advertências e multas por infração do regimento.

A festa até as 3h, o cachorro sujando o hall, a obra sem aviso: o
síndico notifica o apartamento, que tem prazo para se defender; depois
da defesa (ou do fim do prazo), o síndico mantém ou anula, sempre com o
motivo. A multa mantida vira cobrança do apartamento. Código Civil, art.
1.336, § 2º (até 5 vezes a contribuição mensal) e art. 1.337 (o
reincidente).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.tempo import hoje_local
from app.models.condominio import Unidade
from app.models.enums import (
    CanalVerificacao, OrigemCobranca, Papel, StatusCobranca, StatusInfracao, StatusUsuario,
    TipoInfracao,
)
from app.models.financeiro import Cobranca
from app.models.infracao import Infracao
from app.models.usuario import Usuario
from app.schemas.infracao import DecisaoEntrada, DefesaEntrada, InfracaoEntrada, InfracaoSaida
from app.services import notificacao, registro

router = APIRouter(prefix="/infracoes", tags=["Advertências e multas"])

# Código Civil, art. 1.336, § 2º: a multa vai até 5 vezes a contribuição.
LIMITE_VEZES_TAXA = 5
# A multa mantida vence daqui a tantos dias.
VENCIMENTO_MULTA_DIAS = 15
ABERTAS = (StatusInfracao.NOTIFICADA, StatusInfracao.DEFESA_APRESENTADA)
ROTULO = {TipoInfracao.ADVERTENCIA: "advertência", TipoInfracao.MULTA: "multa"}


def _hoje() -> date:
    return hoje_local()


def _reais(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _moradores(db: Session, unidade_id: int) -> list[Usuario]:
    """Quem responde pelo apartamento — quem mora e o dono que não mora:
    a multa é dívida do condômino."""
    return list(db.scalars(select(Usuario).where(
        Usuario.unidade_id == unidade_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
    )).all())


def _sindicos(db: Session, condominio_id: int) -> list[Usuario]:
    return list(db.scalars(select(Usuario).where(
        Usuario.condominio_id == condominio_id, Usuario.papel == Papel.SINDICO,
        Usuario.status == StatusUsuario.ATIVO,
    )).all())


def _avisar(destinos: list[Usuario], titulo: str, mensagem: str) -> None:
    for u in destinos:
        notificacao.notificar(u.email, CanalVerificacao.EMAIL, titulo, mensagem)


def _taxa_mensal(db: Session, unidade_id: int) -> Decimal | None:
    """A contribuição mensal do apartamento: a taxa mais recente lançada."""
    return db.scalar(
        select(Cobranca.valor).where(
            Cobranca.unidade_id == unidade_id, Cobranca.origem == OrigemCobranca.TAXA,
            Cobranca.status != StatusCobranca.CANCELADA,
        ).order_by(Cobranca.competencia.desc()).limit(1)
    )


def _reincidencias(db: Session, inf: Infracao) -> int:
    return db.scalar(select(func.count()).select_from(Infracao).where(
        Infracao.unidade_id == inf.unidade_id, Infracao.id != inf.id,
        Infracao.status == StatusInfracao.CONFIRMADA,
        Infracao.ocorrida_em >= _hoje() - timedelta(days=365),
    )) or 0


def _do_morador(morador: Usuario):
    """As do apartamento desde que o morador está nele: quem chegou
    depois não vê as do morador anterior."""
    return and_(Infracao.unidade_id == morador.unidade_id,
                Infracao.criado_em >= morador.unidade_desde)


def _saida(db: Session, inf: Infracao, usuario: Usuario) -> InfracaoSaida:
    hoje = _hoje()
    return InfracaoSaida(
        id=inf.id, unidade_id=inf.unidade_id, unidade=inf.unidade.identificacao, tipo=inf.tipo,
        descricao=inf.descricao, artigo=inf.artigo, ocorrida_em=inf.ocorrida_em, valor=inf.valor,
        prazo_defesa=inf.prazo_defesa, status=inf.status, defesa=inf.defesa,
        defesa_em=inf.defesa_em,
        defesa_por_nome=inf.defesa_por.nome if inf.defesa_por else None,
        decisao_motivo=inf.decisao_motivo, decidida_em=inf.decidida_em,
        cobranca_id=inf.cobranca_id,
        aplicada_por_nome=inf.aplicada_por.nome if inf.aplicada_por else None,
        reincidencias=_reincidencias(db, inf), criado_em=inf.criado_em,
        pode_defender=(usuario.papel == Papel.MORADOR and inf.status == StatusInfracao.NOTIFICADA
                       and hoje <= inf.prazo_defesa),
        pode_decidir=(usuario.papel == Papel.SINDICO and (
            inf.status == StatusInfracao.DEFESA_APRESENTADA
            or (inf.status == StatusInfracao.NOTIFICADA and hoje > inf.prazo_defesa))),
    )


def _carregar(db: Session, usuario: Usuario, infracao_id: int) -> Infracao:
    """Travada até o commit: a defesa e a decisão não passam juntas."""
    inf = db.get(Infracao, infracao_id, with_for_update=True)
    visivel = inf is not None and inf.condominio_id == usuario.condominio_id and (
        usuario.papel == Papel.SINDICO
        or (usuario.papel == Papel.MORADOR and inf.unidade_id == usuario.unidade_id
            and inf.criado_em >= usuario.unidade_desde)
    )
    if not visivel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Notificação não encontrada.")
    return inf


@router.post("", response_model=InfracaoSaida, status_code=status.HTTP_201_CREATED,
             summary="Notifica um apartamento (advertência ou multa)")
def notificar(
    dados: InfracaoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> InfracaoSaida:
    unidade = db.get(Unidade, dados.unidade_id)
    if unidade is None or unidade.condominio_id != sindico.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Apartamento não encontrado.")
    if dados.tipo == TipoInfracao.MULTA:
        taxa = _taxa_mensal(db, unidade.id)
        if taxa is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lance a taxa mensal do apartamento antes: a multa vai até 5 vezes a "
                       "contribuição mensal (Código Civil, art. 1.336, § 2º).")
        limite = taxa * LIMITE_VEZES_TAXA
        if dados.valor > limite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A multa vai até 5 vezes a contribuição mensal do apartamento "
                       f"({_reais(limite)}), pelo Código Civil, art. 1.336, § 2º.")

    inf = Infracao(
        condominio_id=sindico.condominio_id, unidade_id=unidade.id, aplicada_por_id=sindico.id,
        tipo=dados.tipo, descricao=dados.descricao, artigo=dados.artigo,
        ocorrida_em=dados.ocorrida_em, valor=dados.valor,
        prazo_defesa=_hoje() + timedelta(days=dados.prazo_defesa_dias),
        status=StatusInfracao.NOTIFICADA,
    )
    db.add(inf)
    db.flush()
    registro.registrar(db, sindico, registro.CRIOU, registro.INFRACAO, inf.id,
                       f"{ROTULO[inf.tipo].capitalize()} ao apartamento {unidade.identificacao}")
    db.commit()
    db.refresh(inf)

    detalhe = f" ({inf.artigo})" if inf.artigo else ""
    valor = f" Valor da multa: {_reais(inf.valor)}." if inf.valor else ""
    _avisar(_moradores(db, unidade.id),
            "Notificação de multa" if inf.tipo == TipoInfracao.MULTA else "Advertência do condomínio",
            f"O apartamento {unidade.identificacao} recebeu uma {ROTULO[inf.tipo]} do síndico"
            f"{detalhe}: {inf.descricao}{valor} Você pode apresentar a sua defesa pelo SmartCondo "
            f"até {inf.prazo_defesa:%d/%m/%Y}.")
    return _saida(db, inf, sindico)


@router.get("", response_model=list[InfracaoSaida], summary="Advertências e multas")
def listar(
    status_: StatusInfracao | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_papel(Papel.SINDICO, Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> list[InfracaoSaida]:
    """O síndico vê as do condomínio; o morador, as do apartamento — a
    portaria não."""
    if usuario.condominio_id is None:
        return []
    consulta = (
        select(Infracao)
        .options(selectinload(Infracao.unidade), selectinload(Infracao.defesa_por),
                 selectinload(Infracao.aplicada_por))
        .where(Infracao.condominio_id == usuario.condominio_id)
    )
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(_do_morador(usuario))
    if status_ is not None:
        consulta = consulta.where(Infracao.status == status_)
    lista = db.scalars(consulta.order_by(Infracao.criado_em.desc()).limit(300)).all()
    return [_saida(db, inf, usuario) for inf in lista]


@router.post("/{infracao_id}/defesa", response_model=InfracaoSaida,
             summary="Apresenta a defesa do apartamento")
def defender(
    infracao_id: int,
    dados: DefesaEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> InfracaoSaida:
    inf = _carregar(db, morador, infracao_id)
    if inf.status != StatusInfracao.NOTIFICADA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A defesa desta notificação já foi apresentada ou decidida.")
    if _hoje() > inf.prazo_defesa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O prazo de defesa terminou em {inf.prazo_defesa:%d/%m/%Y}. Fale com o "
                   "síndico.")
    inf.defesa = dados.texto
    inf.defesa_em = datetime.now(timezone.utc)
    inf.defesa_por_id = morador.id
    inf.status = StatusInfracao.DEFESA_APRESENTADA
    registro.registrar(db, morador, registro.EDITOU, registro.INFRACAO, inf.id,
                       "Defesa apresentada")
    db.commit()
    db.refresh(inf)
    _avisar(_sindicos(db, inf.condominio_id), "Defesa apresentada",
            f"O apartamento {inf.unidade.identificacao} apresentou defesa à {ROTULO[inf.tipo]} "
            f"de {inf.ocorrida_em:%d/%m/%Y}. Decida pelo SmartCondo.")
    return _saida(db, inf, morador)


@router.post("/{infracao_id}/decisao", response_model=InfracaoSaida,
             summary="Mantém ou anula, com o motivo")
def decidir(
    infracao_id: int,
    dados: DecisaoEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> InfracaoSaida:
    inf = _carregar(db, sindico, infracao_id)
    if inf.status not in ABERTAS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta notificação já foi decidida.")
    hoje = _hoje()
    if inf.status == StatusInfracao.NOTIFICADA and hoje <= inf.prazo_defesa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O apartamento tem até {inf.prazo_defesa:%d/%m/%Y} para se defender: decida "
                   "depois da defesa ou do fim do prazo.")

    inf.decisao_motivo = dados.motivo
    inf.decidida_em = datetime.now(timezone.utc)
    inf.decidida_por_id = sindico.id
    if dados.manter:
        inf.status = StatusInfracao.CONFIRMADA
        if inf.tipo == TipoInfracao.MULTA:
            cobranca = Cobranca(
                unidade_id=inf.unidade_id, competencia=hoje.replace(day=1),
                descricao=f"Multa — {inf.artigo or 'infração ao regimento'}"[:180],
                valor=inf.valor, vencimento=hoje + timedelta(days=VENCIMENTO_MULTA_DIAS),
                status=StatusCobranca.ABERTA, origem=OrigemCobranca.MULTA,
            )
            db.add(cobranca)
            db.flush()
            inf.cobranca_id = cobranca.id
            registro.registrar(db, sindico, registro.CRIOU, registro.COBRANCA, cobranca.id,
                               f"Multa da notificação {inf.id}")
    else:
        inf.status = StatusInfracao.ANULADA
    registro.registrar(db, sindico, registro.EDITOU, registro.INFRACAO, inf.id,
                       f"{'Mantida' if dados.manter else 'Anulada'}: {dados.motivo}")
    db.commit()
    db.refresh(inf)

    if dados.manter:
        cobrar = (f" A multa de {_reais(inf.valor)} entrou nas cobranças do apartamento, com "
                  f"vencimento em {(hoje + timedelta(days=VENCIMENTO_MULTA_DIAS)):%d/%m/%Y}."
                  if inf.tipo == TipoInfracao.MULTA else "")
        _avisar(_moradores(db, inf.unidade_id), f"{ROTULO[inf.tipo].capitalize()} mantida",
                f"O síndico manteve a {ROTULO[inf.tipo]} de {inf.ocorrida_em:%d/%m/%Y}. "
                f"Motivo: {dados.motivo}{cobrar}")
    else:
        _avisar(_moradores(db, inf.unidade_id), f"{ROTULO[inf.tipo].capitalize()} anulada",
                f"O síndico anulou a {ROTULO[inf.tipo]} de {inf.ocorrida_em:%d/%m/%Y}. "
                f"Motivo: {dados.motivo}")
    return _saida(db, inf, sindico)
