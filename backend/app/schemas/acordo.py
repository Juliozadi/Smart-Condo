"""Schemas do acordo de parcelamento."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from pydantic import Field, field_validator

from app.core.tempo import hoje_local
from app.models.enums import OrigemCobranca, StatusCobranca
from app.schemas.comuns import SchemaBase, vazio_e_nada

# Até quando a primeira parcela pode ficar para depois.
PRIMEIRA_PARCELA_MAX_DIAS = 90


class AcordoEntrada(SchemaBase):
    unidade_id: int = Field(ge=1)
    # As cobranças vencidas do apartamento que entram no acordo.
    cobranca_ids: list[int] = Field(min_length=1, max_length=60)
    parcelas: int = Field(ge=1, le=24)
    primeiro_vencimento: date
    # Multa e juros perdoados no acordo (fica registrado).
    dispensar_encargos: bool = False
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("observacao", mode="before")(vazio_e_nada)

    @field_validator("cobranca_ids")
    @classmethod
    def sem_repetir(cls, ids: list[int]) -> list[int]:
        if len(set(ids)) != len(ids) or any(i < 1 for i in ids):
            raise ValueError("Escolha cada cobrança uma vez só.")
        return ids

    @field_validator("primeiro_vencimento")
    @classmethod
    def vencimento_razoavel(cls, dia: date) -> date:
        hoje = hoje_local()
        if dia < hoje:
            raise ValueError("A primeira parcela não pode vencer no passado.")
        if dia > hoje + timedelta(days=PRIMEIRA_PARCELA_MAX_DIAS):
            raise ValueError("A primeira parcela vence em até 90 dias.")
        return dia


class CancelamentoAcordo(SchemaBase):
    motivo: str = Field(min_length=3, max_length=300)


class CobrancaDoAcordo(SchemaBase):
    id: int
    descricao: str
    valor: Decimal
    vencimento: date
    status: StatusCobranca
    origem: OrigemCobranca
    total_pago: Decimal


class AcordoSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    principal: Decimal
    encargos: Decimal
    total: Decimal
    dispensou_encargos: bool
    parcelas: int
    primeiro_vencimento: date
    observacao: str | None = None
    criado_por_nome: str | None = None
    criado_em: datetime
    cancelado_em: datetime | None = None
    motivo_cancelamento: str | None = None
    # em_dia, em_atraso, quitado ou cancelado.
    situacao: str
    negociadas: list[CobrancaDoAcordo]
    lista_parcelas: list[CobrancaDoAcordo]
    # Desfaz-se só antes de qualquer parcela ser paga (e só o síndico).
    pode_cancelar: bool = False
