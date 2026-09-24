"""Cobranças, pagamentos e preferência de cobrança.

Documentação, seção 6 (História do Usuário — morador e síndico).
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, contains_eager

from app.api.deps import exigir_condominio, exigir_papel, exigir_permissao_porteiro
from app.core.database import get_db
from app.core.tempo import hoje_local
from app.models.condominio import Unidade
from app.models.enums import Papel, StatusCobranca
from app.models.financeiro import Cobranca, Pagamento, PreferenciaCobranca
from app.models.usuario import Usuario
from app.schemas.financeiro import (
    CobrancaEntrada, CobrancaSaida, PagamentoEntrada, PagamentoSaida,
    PreferenciaCobrancaEntrada, PreferenciaCobrancaSaida, ResumoFinanceiro,
)
from app.services import notificacao
from app.models.enums import CanalVerificacao

router = APIRouter(prefix="/financeiro", tags=["Financeiro"])

ZERO = Decimal("0.00")


def _hoje() -> date:
    return hoje_local()


def _total_pago(db: Session, cobranca_id: int) -> Decimal:
    """Soma os pagamentos no banco.

    Ler pela relacionamento `cobranca.pagamentos` nao serve logo depois de
    inserir um pagamento: a coleção já foi carregada antes do flush e fica
    desatualizada, o que fazia a cobrança quitada continuar em aberto.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(Pagamento.valor), 0)).where(
            Pagamento.cobranca_id == cobranca_id
        )
    )
    return Decimal(total or 0)


def _totais_pagos(db: Session, ids: list[int]) -> dict[int, Decimal]:
    """O total pago de várias cobranças numa consulta só. Somar uma a uma
    fazia a lista de um ano de um prédio passar de mil consultas."""
    if not ids:
        return {}
    linhas = db.execute(
        select(Pagamento.cobranca_id, func.sum(Pagamento.valor))
        .where(Pagamento.cobranca_id.in_(ids))
        .group_by(Pagamento.cobranca_id)
    ).all()
    return {cobranca_id: Decimal(total) for cobranca_id, total in linhas}


def _cobranca_saida(db: Session, c: Cobranca, total_pago: Decimal | None = None) -> CobrancaSaida:
    return CobrancaSaida(
        id=c.id, unidade_id=c.unidade_id, unidade=c.unidade.identificacao,
        competencia=c.competencia, descricao=c.descricao, valor=c.valor,
        vencimento=c.vencimento, status=c.status,
        total_pago=_total_pago(db, c.id) if total_pago is None else total_pago,
        criado_em=c.criado_em,
    )


def _dia_de_vencimento(db: Session, unidade_id: int, competencia: date) -> date:
    """Usa o dia que o morador escolheu (seção 6)."""
    morador = db.scalar(
        select(Usuario).where(Usuario.unidade_id == unidade_id, Usuario.papel == Papel.MORADOR)
    )
    dia = 10
    if morador is not None:
        preferencia = db.scalar(
            select(PreferenciaCobranca).where(PreferenciaCobranca.morador_id == morador.id)
        )
        if preferencia is not None:
            dia = preferencia.dia_vencimento

    # O dia é limitado a 28 na entrada, mas o clamp protege dados antigos.
    ultimo_dia = calendar.monthrange(competencia.year, competencia.month)[1]
    return date(competencia.year, competencia.month, min(dia, ultimo_dia))


# ── Preferência do morador (seção 6) ─────────────────────────────────
@router.get(
    "/preferencia",
    response_model=PreferenciaCobrancaSaida,
    summary="Consulta a preferência de cobrança",
)
def consultar_preferencia(
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)), db: Session = Depends(get_db)
) -> PreferenciaCobrancaSaida:
    preferencia = db.scalar(
        select(PreferenciaCobranca).where(PreferenciaCobranca.morador_id == morador.id)
    )
    if preferencia is None:
        # Ainda sem escolha: devolve o padrão, sem gravar nada.
        return PreferenciaCobrancaSaida(morador_id=morador.id)
    return PreferenciaCobrancaSaida(
        morador_id=morador.id,
        dia_vencimento=preferencia.dia_vencimento,
        forma_preferida=preferencia.forma_preferida,
    )


@router.put(
    "/preferencia",
    response_model=PreferenciaCobrancaSaida,
    summary="Escolhe o dia e a forma de pagamento",
)
def definir_preferencia(
    dados: PreferenciaCobrancaEntrada,
    morador: Usuario = Depends(exigir_papel(Papel.MORADOR)),
    db: Session = Depends(get_db),
) -> PreferenciaCobrancaSaida:
    """"uma cobrança mensal na data em que eu escolhesse" (seção 6)."""
    preferencia = db.scalar(
        select(PreferenciaCobranca).where(PreferenciaCobranca.morador_id == morador.id)
    )
    if preferencia is None:
        preferencia = PreferenciaCobranca(morador_id=morador.id)
        db.add(preferencia)

    preferencia.dia_vencimento = dados.dia_vencimento
    preferencia.forma_preferida = dados.forma_preferida

    db.commit()
    db.refresh(preferencia)
    return PreferenciaCobrancaSaida(
        morador_id=morador.id,
        dia_vencimento=preferencia.dia_vencimento,
        forma_preferida=preferencia.forma_preferida,
    )


# ── Cobranças ────────────────────────────────────────────────────────
@router.post(
    "/cobrancas",
    response_model=CobrancaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Gera uma cobrança",
)
def gerar_cobranca(
    dados: CobrancaEntrada,
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> CobrancaSaida:
    unidade = db.get(Unidade, dados.unidade_id)
    if unidade is None or unidade.condominio_id != sindico.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada."
        )

    competencia = dados.competencia.replace(day=1)
    ja_existe = db.scalar(
        select(Cobranca).where(
            Cobranca.unidade_id == unidade.id, Cobranca.competencia == competencia
        )
    )
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe cobrança desta unidade para esta competência.",
        )

    vencimento = dados.vencimento or _dia_de_vencimento(db, unidade.id, competencia)
    cobranca = Cobranca(
        unidade_id=unidade.id,
        competencia=competencia,
        descricao=dados.descricao,
        valor=dados.valor,
        vencimento=vencimento,
        status=StatusCobranca.VENCIDA if vencimento < _hoje() else StatusCobranca.ABERTA,
    )
    db.add(cobranca)
    db.commit()
    db.refresh(cobranca)
    return _cobranca_saida(db, cobranca)


@router.get("/cobrancas", response_model=list[CobrancaSaida], summary="Lista as cobranças")
def listar_cobrancas(
    status_cobranca: StatusCobranca | None = Query(default=None, alias="status"),
    usuario: Usuario = Depends(exigir_condominio),
    db: Session = Depends(get_db),
) -> list[CobrancaSaida]:
    consulta = (
        select(Cobranca).join(Unidade)
        .options(contains_eager(Cobranca.unidade))
        .where(Unidade.condominio_id == usuario.condominio_id)
    )
    # O morador vê apenas as cobranças da própria unidade.
    if usuario.papel == Papel.MORADOR:
        consulta = consulta.where(Cobranca.unidade_id == usuario.unidade_id)
    elif usuario.papel == Papel.PORTEIRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O financeiro é do síndico e dos moradores.",
        )
    if status_cobranca is not None:
        consulta = consulta.where(Cobranca.status == status_cobranca)

    # Uma cobrança em aberto que passou do vencimento aparece como vencida.
    # Um UPDATE só, antes de ler: marcar uma a uma e commitar depois de ler
    # expirava os objetos, e cada cobrança era relida do banco — mais de
    # mil consultas para a lista de um ano de um prédio.
    marcadas = db.execute(
        update(Cobranca)
        .where(
            Cobranca.status == StatusCobranca.ABERTA,
            Cobranca.vencimento < _hoje(),
            Cobranca.unidade_id.in_(
                select(Unidade.id).where(Unidade.condominio_id == usuario.condominio_id)
            ),
        )
        .values(status=StatusCobranca.VENCIDA)
        .execution_options(synchronize_session=False)
    )
    if marcadas.rowcount:
        db.commit()

    cobrancas = db.scalars(consulta.order_by(Cobranca.competencia.desc())).all()

    totais = _totais_pagos(db, [c.id for c in cobrancas])
    return [_cobranca_saida(db, c, totais.get(c.id, ZERO)) for c in cobrancas]


# ── Pagamentos ───────────────────────────────────────────────────────
@router.post(
    "/cobrancas/{cobranca_id}/pagamentos",
    response_model=PagamentoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um pagamento",
)
def registrar_pagamento(
    cobranca_id: int,
    dados: PagamentoEntrada,
    usuario: Usuario = Depends(exigir_papel(Papel.MORADOR, Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> PagamentoSaida:
    # Travada até o fim da transação: dois pagamentos simultâneos (clique
    # duplo, duas abas) passariam juntos pela conferência do que falta
    # pagar, e a cobrança ficaria paga a mais.
    cobranca = db.get(Cobranca, cobranca_id, with_for_update=True)
    if cobranca is None or cobranca.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada."
        )
    if usuario.papel == Papel.MORADOR and cobranca.unidade_id != usuario.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada."
        )
    if cobranca.status == StatusCobranca.PAGA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta cobrança já está paga."
        )
    if cobranca.status == StatusCobranca.CANCELADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta cobrança foi cancelada."
        )

    restante = cobranca.valor - _total_pago(db, cobranca.id)
    if dados.valor > restante:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O valor passa do que falta pagar (R$ {restante}).",
        )

    agora = datetime.now(timezone.utc)
    pagamento = Pagamento(
        cobranca_id=cobranca.id,
        pago_por_id=usuario.id,
        valor=dados.valor,
        forma=dados.forma,
        pago_em=agora,
        comprovante_url=dados.comprovante_url,
        observacao=dados.observacao,
    )
    db.add(pagamento)
    db.flush()

    # Quitou: a cobrança fecha.
    if _total_pago(db, cobranca.id) >= cobranca.valor:
        cobranca.status = StatusCobranca.PAGA

    db.commit()
    db.refresh(pagamento)

    # "o próprio sistema me notificar com qual meio o pagamento foi realizado,
    # por quem e a data do pagamento" (seção 6).
    sindico = db.scalar(
        select(Usuario).where(
            Usuario.condominio_id == usuario.condominio_id, Usuario.papel == Papel.SINDICO
        )
    )
    if sindico is not None:
        notificacao.notificar(
            sindico.email, CanalVerificacao.EMAIL,
            "Pagamento recebido",
            f"Unidade {cobranca.unidade.identificacao}: R$ {pagamento.valor} "
            f"por {pagamento.forma.value}, pago por {usuario.nome} "
            f"em {pagamento.pago_em:%d/%m/%Y}.",
        )

    return PagamentoSaida(
        id=pagamento.id, cobranca_id=pagamento.cobranca_id, valor=pagamento.valor,
        forma=pagamento.forma, pago_em=pagamento.pago_em, pago_por_id=usuario.id,
        pago_por_nome=usuario.nome, comprovante_url=pagamento.comprovante_url,
        observacao=pagamento.observacao,
    )


@router.get(
    "/cobrancas/{cobranca_id}/pagamentos",
    response_model=list[PagamentoSaida],
    summary="Histórico de pagamentos de uma cobrança",
)
def listar_pagamentos(
    cobranca_id: int,
    usuario: Usuario = Depends(exigir_papel(Papel.MORADOR, Papel.SINDICO)),
    db: Session = Depends(get_db),
) -> list[PagamentoSaida]:
    cobranca = db.get(Cobranca, cobranca_id)
    if cobranca is None or cobranca.unidade.condominio_id != usuario.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada."
        )
    if usuario.papel == Papel.MORADOR and cobranca.unidade_id != usuario.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada."
        )

    return [
        PagamentoSaida(
            id=p.id, cobranca_id=p.cobranca_id, valor=p.valor, forma=p.forma,
            pago_em=p.pago_em, pago_por_id=p.pago_por_id,
            pago_por_nome=p.pago_por.nome if p.pago_por else None,
            comprovante_url=p.comprovante_url, observacao=p.observacao,
        )
        for p in sorted(cobranca.pagamentos, key=lambda x: x.pago_em)
    ]


# ── Resumo do síndico ────────────────────────────────────────────────
@router.get("/resumo", response_model=ResumoFinanceiro, summary="Indicadores do condomínio")
def resumo(
    sindico: Usuario = Depends(exigir_papel(Papel.SINDICO)), db: Session = Depends(get_db)
) -> ResumoFinanceiro:
    cobrancas = db.scalars(
        select(Cobranca).join(Unidade).where(Unidade.condominio_id == sindico.condominio_id)
    ).all()

    hoje = _hoje()
    total_aberto = total_vencido = total_recebido = ZERO
    abertas = 0
    inadimplentes: set[int] = set()

    totais = _totais_pagos(db, [c.id for c in cobrancas])
    for c in cobrancas:
        pago = totais.get(c.id, ZERO)
        total_recebido += pago
        if c.status in (StatusCobranca.ABERTA, StatusCobranca.VENCIDA):
            falta = c.valor - pago
            total_aberto += falta
            abertas += 1
            if c.vencimento < hoje:
                total_vencido += falta
                inadimplentes.add(c.unidade_id)

    return ResumoFinanceiro(
        total_aberto=total_aberto,
        total_vencido=total_vencido,
        total_recebido=total_recebido,
        cobrancas_abertas=abertas,
        unidades_inadimplentes=len(inadimplentes),
    )
