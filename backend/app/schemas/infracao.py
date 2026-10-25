"""Schemas das advertências e multas."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import StatusInfracao, TipoInfracao
from app.schemas.comuns import SchemaBase


class InfracaoEntrada(SchemaBase):
    unidade_id: int
    tipo: TipoInfracao
    descricao: str = Field(min_length=10, max_length=2000)
    artigo: str | None = Field(default=None, max_length=120)
    ocorrida_em: date
    valor: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    # Dias para o apartamento apresentar a defesa.
    prazo_defesa_dias: int = Field(default=10, ge=5, le=30)

    @field_validator("ocorrida_em")
    @classmethod
    def no_passado_recente(cls, valor: date) -> date:
        hoje = hoje_local()
        if valor > hoje:
            raise ValueError("A data da infração não pode estar no futuro.")
        if valor < hoje - timedelta(days=365):
            raise ValueError("A infração precisa ter acontecido no último ano.")
        return valor

    @field_validator("artigo")
    @classmethod
    def vazio_vira_nulo(cls, valor: str | None) -> str | None:
        return valor or None

    @model_validator(mode="after")
    def valor_conforme_o_tipo(self) -> "InfracaoEntrada":
        if self.tipo == TipoInfracao.MULTA and self.valor is None:
            raise ValueError("Informe o valor da multa.")
        if self.tipo == TipoInfracao.ADVERTENCIA and self.valor is not None:
            raise ValueError("A advertência não tem valor; para cobrar, escolha multa.")
        return self


class DefesaEntrada(SchemaBase):
    texto: str = Field(min_length=10, max_length=4000)


class DecisaoEntrada(SchemaBase):
    manter: bool
    # A decisão sempre explica: o apartamento tem o direito de saber por quê.
    motivo: str = Field(min_length=3, max_length=2000)


class InfracaoSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    tipo: TipoInfracao
    descricao: str
    artigo: str | None = None
    ocorrida_em: date
    valor: Decimal | None = None
    prazo_defesa: date
    status: StatusInfracao
    defesa: str | None = None
    defesa_em: datetime | None = None
    defesa_por_nome: str | None = None
    decisao_motivo: str | None = None
    decidida_em: datetime | None = None
    cobranca_id: int | None = None
    aplicada_por_nome: str | None = None
    # Quantas outras o apartamento teve mantidas nos últimos 12 meses
    # (art. 1.337: o reincidente).
    reincidencias: int = 0
    pode_defender: bool = False
    pode_decidir: bool = False
    criado_em: datetime
