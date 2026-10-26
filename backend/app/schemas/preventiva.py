"""Schemas da manutenção preventiva."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.schemas.comuns import SchemaBase

Situacao = Literal["vencida", "vence_em_breve", "em_dia"]
# Um vencimento ou uma realização a mais de 10 anos de hoje é erro de digitação.
LIMITE_ANOS = 10


def _vazio_e_nada(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


def _vencimento_razoavel(dia: date | None) -> date | None:
    if dia is not None and abs((dia - hoje_local()).days) > LIMITE_ANOS * 366:
        raise ValueError(f"O vencimento precisa estar a menos de {LIMITE_ANOS} anos de hoje.")
    return dia


class PlanoEntrada(SchemaBase):
    nome: str = Field(min_length=3, max_length=120)
    periodicidade_meses: int = Field(ge=1, le=120)
    proximo_vencimento: date
    antecedencia_aviso_dias: int = Field(default=30, ge=0, le=180)
    fornecedor: str | None = Field(default=None, max_length=120)
    observacao: str | None = Field(default=None, max_length=2000)

    _vazios = field_validator("fornecedor", "observacao", mode="before")(_vazio_e_nada)
    _vencimento = field_validator("proximo_vencimento")(_vencimento_razoavel)


class PlanoAtualizacao(SchemaBase):
    """Só o que veio muda; fornecedor e observação podem ser apagados."""
    nome: str | None = Field(default=None, min_length=3, max_length=120)
    periodicidade_meses: int | None = Field(default=None, ge=1, le=120)
    proximo_vencimento: date | None = None
    antecedencia_aviso_dias: int | None = Field(default=None, ge=0, le=180)
    fornecedor: str | None = Field(default=None, max_length=120)
    observacao: str | None = Field(default=None, max_length=2000)

    _vazios = field_validator("fornecedor", "observacao", mode="before")(_vazio_e_nada)
    _vencimento = field_validator("proximo_vencimento")(_vencimento_razoavel)


class PlanoSaida(SchemaBase):
    id: int
    nome: str
    periodicidade_meses: int
    proximo_vencimento: date
    antecedencia_aviso_dias: int
    fornecedor: str | None = None
    observacao: str | None = None
    ultima_realizacao: date | None = None
    situacao: Situacao
    # Negativo: venceu há tantos dias.
    dias_para_vencer: int


class RealizacaoEntrada(SchemaBase):
    data: date
    custo: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    observacao: str | None = Field(default=None, max_length=2000)
    # Lança o custo como despesa de manutenção na prestação de contas.
    lancar_despesa: bool = False

    _observacao = field_validator("observacao", mode="before")(_vazio_e_nada)

    @field_validator("data")
    @classmethod
    def _data(cls, dia: date) -> date:
        hoje = hoje_local()
        if dia > hoje:
            raise ValueError("Registre depois de feito: a data não pode ser futura.")
        if dia < hoje - timedelta(days=LIMITE_ANOS * 366):
            raise ValueError(f"A data não pode ser de mais de {LIMITE_ANOS} anos atrás.")
        return dia

    @model_validator(mode="after")
    def _despesa(self):
        if self.lancar_despesa and self.custo is None:
            raise ValueError("Para lançar a despesa, informe o custo.")
        # Como na prestação de contas: despesa de mais de 5 anos não entra.
        if self.lancar_despesa and self.data < hoje_local() - timedelta(days=5 * 366):
            raise ValueError("A despesa não pode ser de mais de 5 anos atrás.")
        return self


class RealizacaoSaida(SchemaBase):
    id: int
    data: date
    custo: Decimal | None = None
    observacao: str | None = None
    registrada_por_nome: str | None = None
    despesa_id: int | None = None
    criado_em: datetime
