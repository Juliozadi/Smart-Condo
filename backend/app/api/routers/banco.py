"""O que o próprio banco calcula, na tela do síndico.

Visões, função de rateio e o log que o gatilho grava a cada mudança de
cobrança (app/core/objetos_banco.py, instalados pela migração
d8e9f0a1b2c3). Tudo filtrado pelo condomínio do síndico, e por
parâmetro, nunca por texto montado.
"""
from __future__ import annotations

from decimal import Decimal

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.api.deps import exigir_papel
from app.core.database import get_db
from app.models.enums import Papel
from app.models.usuario import Usuario
from app.schemas.banco import AlteracaoDeCobranca, MesDoBalancete, ParteDoRateio, SituacaoUnidade

router = APIRouter(prefix="/banco", tags=["Banco de dados"])
so_sindico = exigir_papel(Papel.SINDICO)


@router.get("/situacao-unidades", response_model=list[SituacaoUnidade],
            summary="Situação de cada apartamento (visão vw_situacao_unidades)")
def situacao_unidades(sindico: Usuario = Depends(so_sindico),
                      db: Session = Depends(get_db)) -> list[SituacaoUnidade]:
    linhas = db.execute(text("""
        SELECT v.*
          FROM vw_situacao_unidades v
          JOIN unidades u ON u.id = v.unidade_id
         WHERE u.condominio_id = :condominio
         ORDER BY u.bloco, u.numero
    """), {"condominio": sindico.condominio_id}).mappings().all()
    return [SituacaoUnidade(**linha) for linha in linhas]


@router.get("/balancete", response_model=list[MesDoBalancete],
            summary="Receitas, despesas e saldo por mês (visão vw_balancete_mensal)")
def balancete(sindico: Usuario = Depends(so_sindico),
              db: Session = Depends(get_db)) -> list[MesDoBalancete]:
    linhas = db.execute(text("""
        SELECT mes, receitas, despesas, saldo_do_mes, saldo_acumulado
          FROM vw_balancete_mensal
         WHERE condominio_id = :condominio
         ORDER BY mes
    """), {"condominio": sindico.condominio_id}).mappings().all()
    return [MesDoBalancete(**linha) for linha in linhas]


@router.get("/log-cobrancas", response_model=list[AlteracaoDeCobranca],
            summary="Mudanças de cobrança gravadas pelo gatilho trg_log_cobranca")
def log_cobrancas(sindico: Usuario = Depends(so_sindico),
                  db: Session = Depends(get_db)) -> list[AlteracaoDeCobranca]:
    linhas = db.execute(text("""
        SELECT l.id, l.cobranca_id, u.numero AS apartamento, c.descricao,
               l.status_anterior, l.status_novo, l.valor_anterior, l.valor_novo,
               l.vencimento_anterior, l.vencimento_novo, l.alterado_em
          FROM log_cobrancas l
          JOIN cobrancas c ON c.id = l.cobranca_id
          JOIN unidades u ON u.id = c.unidade_id
         WHERE u.condominio_id = :condominio
         ORDER BY l.alterado_em DESC, l.id DESC
         LIMIT 50
    """), {"condominio": sindico.condominio_id}).mappings().all()
    return [AlteracaoDeCobranca(**linha) for linha in linhas]


@router.get("/rateio", response_model=list[ParteDoRateio],
            summary="Divide um total pela fração ideal (função fn_rateio)")
def rateio(
    total: Decimal = Query(gt=0, le=Decimal("10000000"), max_digits=10, decimal_places=2),
    sindico: Usuario = Depends(so_sindico),
    db: Session = Depends(get_db),
) -> list[ParteDoRateio]:
    try:
        linhas = db.execute(text("SELECT * FROM fn_rateio(:condominio, :total)"),
                            {"condominio": sindico.condominio_id, "total": total}).mappings().all()
    except DBAPIError as erro:
        db.rollback()
        # Só as mensagens que a própria função levanta (RAISE EXCEPTION,
        # frações faltando ou que não somam 100%); qualquer outro erro sobe.
        if isinstance(erro.orig, psycopg.errors.RaiseException):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=erro.orig.diag.message_primary) from None
        raise
    return [ParteDoRateio(**linha) for linha in linhas]
