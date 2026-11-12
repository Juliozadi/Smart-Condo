"""O que as visões e as funções do banco devolvem à tela do síndico."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SituacaoUnidade(BaseModel):
    unidade_id: int
    apartamento: str
    fracao_ideal: Decimal | None
    responsavel: str | None
    cobrancas_em_atraso: int
    valor_em_atraso: Decimal
    a_vencer: Decimal
    situacao: str


class MesDoBalancete(BaseModel):
    mes: date
    receitas: Decimal
    despesas: Decimal
    saldo_do_mes: Decimal
    saldo_acumulado: Decimal


class AlteracaoDeCobranca(BaseModel):
    id: int
    cobranca_id: int
    apartamento: str
    descricao: str
    status_anterior: str | None
    status_novo: str | None
    valor_anterior: Decimal | None
    valor_novo: Decimal | None
    vencimento_anterior: date | None
    vencimento_novo: date | None
    alterado_em: datetime


class ParteDoRateio(BaseModel):
    unidade_id: int
    apartamento: str
    fracao: Decimal
    valor: Decimal
