"""Declaração de quitação condominial.

O dono vende o apartamento, e o comprador — e o cartório, na escritura
(Lei 7.433/1985, art. 2º, § 2º) — quer a prova de que não há taxa
atrasada: a dívida de condomínio acompanha o imóvel (Código Civil, art.
1.345). Era um papel assinado pelo síndico, que ninguém conseguia
conferir. Agora o apartamento sem débito vencido emite a declaração, e
qualquer um confere pelo código, sem login e sem ver dado pessoal.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.core.limite import limitar
from app.core.tempo import hoje_local
from app.models.condominio import Condominio, Unidade
from app.models.declaracao import DeclaracaoQuitacao
from app.models.enums import CanalVerificacao, Papel, StatusCobranca, StatusUsuario
from app.models.financeiro import Cobranca, Pagamento
from app.models.usuario import Usuario
from app.schemas.declaracao import (
    DeclaracaoEntrada, DeclaracaoPublica, DeclaracaoSaida, RevogacaoEntrada,
)
from app.services import notificacao, registro
from app.services.quitacao import (
    ALFABETO, TAMANHO_CODIGO, VALIDADE_DIAS, formatar as _formatar, novo_codigo,
)

router = APIRouter(prefix="/declaracoes-quitacao", tags=["Declaração de quitação"])

EM_ABERTO = (StatusCobranca.ABERTA, StatusCobranca.VENCIDA)

morador_ou_sindico = exigir_papel(Papel.MORADOR, Papel.SINDICO)
sindico = exigir_papel(Papel.SINDICO)


def _hoje() -> date:
    return hoje_local()


def _reais(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _situacao(d: DeclaracaoQuitacao, hoje: date) -> str:
    if d.revogada_em is not None:
        return "revogada"
    return "vencida" if hoje > d.valida_ate else "valida"


def _saida(d: DeclaracaoQuitacao, usuario: Usuario, hoje: date) -> DeclaracaoSaida:
    eh_sindico = usuario.papel == Papel.SINDICO
    situacao = _situacao(d, hoje)
    return DeclaracaoSaida(
        id=d.id, codigo=_formatar(d.codigo), unidade=d.identificacao_unidade,
        referencia_ate=d.referencia_ate, valida_ate=d.valida_ate, emitida_em=d.emitida_em,
        situacao=situacao,
        emitida_por_nome=(d.emitida_por.nome if eh_sindico and d.emitida_por else None),
        revogada_em=d.revogada_em, motivo_revogacao=d.motivo_revogacao,
        # A vencida já não vale: não há o que revogar.
        pode_revogar=eh_sindico and situacao == "valida",
    )


def _debitos(db: Session, unidade_id: int, hoje: date) -> tuple[int, Decimal]:
    """As cobranças vencidas e não quitadas do apartamento, e quanto falta.
    Pagamento parcial não quita; a cobrança cancelada não é dívida; a que
    ainda não venceu também não."""
    pago = (
        select(func.coalesce(func.sum(Pagamento.valor - Pagamento.encargos), 0))
        .where(Pagamento.cobranca_id == Cobranca.id)
        .correlate(Cobranca).scalar_subquery()
    )
    linhas = db.execute(
        select(Cobranca.valor - pago).where(
            Cobranca.unidade_id == unidade_id, Cobranca.status.in_(EM_ABERTO),
            Cobranca.vencimento < hoje,
        )
    ).scalars().all()
    return len(linhas), sum((Decimal(v) for v in linhas), Decimal("0"))


@router.post("", response_model=DeclaracaoSaida, status_code=status.HTTP_201_CREATED,
             summary="Emite a declaração de quitação do apartamento")
def emitir(
    dados: DeclaracaoEntrada,
    response: Response,
    usuario: Usuario = Depends(morador_ou_sindico),
    db: Session = Depends(get_db),
) -> DeclaracaoSaida:
    hoje = _hoje()
    if usuario.papel == Papel.MORADOR:
        if dados.unidade_id is not None and dados.unidade_id != usuario.unidade_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Você só emite a declaração do seu apartamento.")
        unidade_id = usuario.unidade_id
    else:
        if dados.unidade_id is None:
            raise HTTPException(status_code=422, detail="Escolha o apartamento.")
        unidade_id = dados.unidade_id

    # A trava no apartamento faz dois pedidos ao mesmo tempo (dois cliques)
    # acharem a mesma declaração, em vez de emitirem duas.
    unidade = db.scalar(select(Unidade).where(Unidade.id == unidade_id).with_for_update())
    if unidade is None or unidade.condominio_id != usuario.condominio_id or unidade.pendente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Apartamento não encontrado.")

    # Pedida de novo no mesmo dia, é a mesma declaração: nada mudou.
    existente = db.scalar(select(DeclaracaoQuitacao).where(
        DeclaracaoQuitacao.unidade_id == unidade.id, DeclaracaoQuitacao.referencia_ate == hoje,
        DeclaracaoQuitacao.revogada_em.is_(None),
    ).options(selectinload(DeclaracaoQuitacao.emitida_por)))
    if existente is not None:
        response.status_code = status.HTTP_200_OK
        return _saida(existente, usuario, hoje)

    quantas, falta = _debitos(db, unidade.id, hoje)
    if quantas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"O apartamento {unidade.identificacao} tem {quantas} "
                    f"{'cobrança vencida' if quantas == 1 else 'cobranças vencidas'} em aberto "
                    f"({_reais(falta)}). Quite antes de emitir a declaração."),
        )

    condominio = db.get(Condominio, unidade.condominio_id)
    responsavel = db.get(Usuario, condominio.sindico_id) if condominio.sindico_id else None
    d = DeclaracaoQuitacao(
        condominio_id=condominio.id, unidade_id=unidade.id, emitida_por_id=usuario.id,
        codigo=novo_codigo(db), referencia_ate=hoje,
        valida_ate=hoje + timedelta(days=VALIDADE_DIAS),
        condominio_nome=condominio.nome, condominio_cnpj=condominio.cnpj,
        identificacao_unidade=unidade.identificacao,
        sindico_nome=responsavel.nome if responsavel else None,
    )
    db.add(d)
    db.flush()
    registro.registrar(db, usuario, registro.CRIOU, registro.DECLARACAO, d.id,
                       f"Declaração de quitação do apartamento {unidade.identificacao}")
    db.commit()
    db.refresh(d)
    return _saida(d, usuario, hoje)


@router.get("", response_model=list[DeclaracaoSaida], summary="Declarações emitidas")
def listar(
    unidade_id: int | None = Query(default=None, ge=1),
    usuario: Usuario = Depends(morador_ou_sindico),
    db: Session = Depends(get_db),
) -> list[DeclaracaoSaida]:
    consulta = (select(DeclaracaoQuitacao)
                .options(selectinload(DeclaracaoQuitacao.emitida_por))
                .where(DeclaracaoQuitacao.condominio_id == usuario.condominio_id))
    if usuario.papel == Papel.MORADOR:
        # Quem chega ao apartamento não vê as do morador anterior.
        consulta = consulta.where(DeclaracaoQuitacao.unidade_id == usuario.unidade_id,
                                  DeclaracaoQuitacao.emitida_em >= usuario.unidade_desde)
    elif unidade_id is not None:
        consulta = consulta.where(DeclaracaoQuitacao.unidade_id == unidade_id)
    hoje = _hoje()
    lista = db.scalars(consulta.order_by(DeclaracaoQuitacao.emitida_em.desc(),
                                         DeclaracaoQuitacao.id.desc()).limit(200)).all()
    return [_saida(d, usuario, hoje) for d in lista]


@router.post("/{declaracao_id}/revogacao", response_model=DeclaracaoSaida,
             summary="O síndico revoga uma declaração, com o motivo")
def revogar(
    declaracao_id: int,
    dados: RevogacaoEntrada,
    usuario: Usuario = Depends(sindico),
    db: Session = Depends(get_db),
) -> DeclaracaoSaida:
    d = db.scalar(select(DeclaracaoQuitacao).where(DeclaracaoQuitacao.id == declaracao_id)
                  .with_for_update())
    if d is None or d.condominio_id != usuario.condominio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Declaração não encontrada.")
    if d.revogada_em is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta declaração já foi revogada.")
    if _situacao(d, _hoje()) == "vencida":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Esta declaração já venceu: não vale mais, não há o que revogar.")
    d.revogada_em = datetime.now(timezone.utc)
    d.revogada_por_id = usuario.id
    d.motivo_revogacao = dados.motivo
    registro.registrar(db, usuario, registro.CANCELOU, registro.DECLARACAO, d.id,
                       f"Revogada: {dados.motivo}")
    db.commit()
    db.refresh(d)

    moradores = db.scalars(select(Usuario).where(
        Usuario.unidade_id == d.unidade_id, Usuario.papel == Papel.MORADOR,
        Usuario.status == StatusUsuario.ATIVO,
    )).all()
    for m in moradores:
        notificacao.notificar(
            m.email, CanalVerificacao.EMAIL, "Declaração de quitação revogada",
            f"A declaração {_formatar(d.codigo)} do apartamento {d.identificacao_unidade}, de "
            f"{d.referencia_ate:%d/%m/%Y}, foi revogada pelo síndico. Motivo: {dados.motivo}",
        )
    return _saida(d, usuario, _hoje())


@router.get("/verificar/{codigo}", response_model=DeclaracaoPublica,
            summary="Confere uma declaração pelo código (aberto, sem login)",
            # 80 bits de código não se adivinham, mas a rota aberta não
            # deve servir de alvo para varredura.
            dependencies=[Depends(limitar("verificar_declaracao", 30))])
def verificar(codigo: str, db: Session = Depends(get_db)) -> DeclaracaoPublica:
    limpo = re.sub(r"[\s-]", "", codigo).upper()
    d = None
    if re.fullmatch(rf"[{ALFABETO}]{{{TAMANHO_CODIGO}}}", limpo):
        d = db.scalar(select(DeclaracaoQuitacao).where(DeclaracaoQuitacao.codigo == limpo))
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Declaração não encontrada. Confira o código.")
    return DeclaracaoPublica(
        codigo=_formatar(d.codigo), condominio_nome=d.condominio_nome,
        condominio_cnpj=d.condominio_cnpj, unidade=d.identificacao_unidade,
        sindico_nome=d.sindico_nome, referencia_ate=d.referencia_ate, valida_ate=d.valida_ate,
        emitida_em=d.emitida_em, situacao=_situacao(d, _hoje()), revogada_em=d.revogada_em,
    )
