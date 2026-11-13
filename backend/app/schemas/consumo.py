"""Medição individual de água e gás: o que entra e o que sai da API."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import TipoConsumo
from app.schemas.comuns import SchemaBase

# Leituras de até dois anos atrás: a planilha antiga do zelador cabe.
MESES_PARA_TRAS = 24


def _competencia(valor: date) -> date:
    valor = valor.replace(day=1)
    hoje = hoje_local()
    if valor > hoje.replace(day=1):
        raise ValueError("A leitura não pode ser de um mês que ainda não chegou.")
    limite = (hoje.replace(day=1) - timedelta(days=MESES_PARA_TRAS * 31)).replace(day=1)
    if valor < limite:
        raise ValueError(f"Registre leituras dos últimos {MESES_PARA_TRAS} meses.")
    return valor


class LeituraItem(SchemaBase):
    unidade_id: int
    leitura: Decimal = Field(ge=0, max_digits=10, decimal_places=3)
    troca_medidor: bool = False


class LeiturasEntrada(SchemaBase):
    tipo: TipoConsumo
    competencia: date
    leituras: list[LeituraItem] = Field(min_length=1, max_length=500)

    _competencia = field_validator("competencia")(_competencia)

    @model_validator(mode="after")
    def _sem_repetir(self) -> "LeiturasEntrada":
        ids = [item.unidade_id for item in self.leituras]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada apartamento aparece uma vez só nas leituras.")
        return self


class LinhaLeitura(SchemaBase):
    unidade_id: int
    apartamento: str
    anterior_competencia: date | None
    anterior_leitura: Decimal | None
    leitura: Decimal | None
    consumo: Decimal | None
    troca_medidor: bool
    acima_do_normal: bool
    # A média dos últimos três consumos, para comparar.
    media: Decimal | None
    cobrada: bool
    valor_cobrado: Decimal | None
    pode_editar: bool


class CobrancaConsumoEntrada(SchemaBase):
    tipo: TipoConsumo
    competencia: date
    # A tarifa da concessionária por m³, com até 4 casas (R$ 9,8765).
    tarifa: Decimal = Field(gt=0, le=1000, max_digits=8, decimal_places=4)
    vencimento: date | None = None

    _competencia = field_validator("competencia")(_competencia)

    @model_validator(mode="after")
    def _vencimento(self) -> "CobrancaConsumoEntrada":
        if self.vencimento is not None:
            if self.vencimento < self.competencia:
                raise ValueError("O vencimento não pode ser antes do mês da leitura.")
            if self.vencimento > hoje_local() + timedelta(days=120):
                raise ValueError("O vencimento pode ser no máximo 120 dias à frente.")
        return self


class HistoricoConsumo(SchemaBase):
    competencia: date
    leitura: Decimal
    consumo: Decimal | None
    troca_medidor: bool
    acima_do_normal: bool
    valor_cobrado: Decimal | None
