"""Achados e perdidos: o que entra e o que sai da API."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from pydantic import Field, field_validator

from app.core.tempo import hoje_local
from app.models.enums import StatusAchado
from app.schemas.comuns import SchemaBase

# Quem acha e só registra dias depois ainda pode; um mês para trás já é
# data digitada errada.
DIAS_PARA_TRAS = 30


class AchadoEntrada(SchemaBase):
    descricao: str = Field(min_length=3, max_length=200)
    local: str = Field(min_length=2, max_length=120)
    encontrado_em: date

    @field_validator("encontrado_em")
    @classmethod
    def _data(cls, valor: date) -> date:
        hoje = hoje_local()
        if valor > hoje:
            raise ValueError("A data em que foi achado não pode estar no futuro.")
        if valor < hoje - timedelta(days=DIAS_PARA_TRAS):
            raise ValueError(f"Registre o que foi achado nos últimos {DIAS_PARA_TRAS} dias.")
        return valor


class DevolucaoEntrada(SchemaBase):
    entregue_a: str = Field(min_length=3, max_length=120)


class DescarteEntrada(SchemaBase):
    destino: str = Field(min_length=3, max_length=300)


class AchadoSaida(SchemaBase):
    id: int
    descricao: str
    local: str
    encontrado_em: date
    status: StatusAchado
    dias_guardado: int
    reclamado: bool
    reclamado_por_mim: bool
    # Só a equipe vê quem registrou, quem reclamou, a quem foi entregue e o
    # destino; o morador vê esses dados apenas do que ele mesmo reclamou.
    registrado_por: str | None = None
    reclamado_por: str | None = None
    reclamado_em: datetime | None = None
    devolvido_em: datetime | None = None
    entregue_a: str | None = None
    descartado_em: datetime | None = None
    destino: str | None = None
    pode_reclamar: bool = False
    pode_desistir: bool = False
    pode_devolver: bool = False
    pode_descartar: bool = False
