"""Schemas do agendamento de mudança."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import StatusMudanca, TipoMudanca
from app.schemas.comuns import SchemaBase

# Até quando se agenda: mais que isso é engano na data.
ANTECEDENCIA_MAXIMA_DIAS = 365


class MudancaEntrada(SchemaBase):
    tipo: TipoMudanca
    data: date
    hora_inicio: time
    hora_fim: time
    empresa: str | None = Field(default=None, max_length=120)
    observacao: str | None = Field(default=None, max_length=300)

    @field_validator("hora_inicio", "hora_fim")
    @classmethod
    def sem_fuso(cls, valor: time) -> time:
        if valor.tzinfo is not None:
            raise ValueError("Informe o horário sem fuso, no horário do condomínio.")
        return valor

    @field_validator("data")
    @classmethod
    def nao_muito_longe(cls, valor: date) -> date:
        if valor > hoje_local() + timedelta(days=ANTECEDENCIA_MAXIMA_DIAS):
            raise ValueError("A mudança pode ser agendada com até um ano de antecedência.")
        return valor

    @field_validator("empresa", "observacao")
    @classmethod
    def vazio_vira_nulo(cls, valor: str | None) -> str | None:
        return valor or None

    @model_validator(mode="after")
    def conferir_intervalo(self) -> "MudancaEntrada":
        if self.hora_fim <= self.hora_inicio:
            raise ValueError("O horário de término precisa ser depois do início.")
        return self


class AvaliacaoMudanca(SchemaBase):
    aprovada: bool
    motivo: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def recusa_tem_motivo(self) -> "AvaliacaoMudanca":
        # O morador precisa saber por que não pode mudar naquele dia.
        if not self.aprovada and not (self.motivo and len(self.motivo) >= 3):
            raise ValueError("Informe o motivo da recusa.")
        return self


class CancelamentoMudanca(SchemaBase):
    motivo: str | None = Field(default=None, max_length=300)


class MudancaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    tipo: TipoMudanca
    data: date
    hora_inicio: time
    hora_fim: time
    empresa: str | None = None
    observacao: str | None = None
    status: StatusMudanca
    solicitada_por_nome: str | None = None
    motivo_recusa: str | None = None
    cancelada_pelo_sindico: bool = False
    motivo_cancelamento: str | None = None
    criado_em: datetime


class HorarioDoDia(SchemaBase):
    inicio: time
    fim: time


class RegrasMudanca(SchemaBase):
    antecedencia_minima_dias: int
    antecedencia_maxima_dias: int
    # Dia da semana (1 = segunda ... 7 = domingo) → horário permitido;
    # o dia que não aparece não tem mudança.
    horarios: dict[int, HorarioDoDia]
