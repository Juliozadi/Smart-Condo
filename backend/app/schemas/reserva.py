"""Schemas de reserva.

Documentação, seção 6: o morador vê que o espaço está ocupado na data e no
horário, mas nunca quem reservou — "eu gostaria que não mostrasse quem
alugou, para evitar conflitos".
"""
from __future__ import annotations

from datetime import date, datetime, time

from pydantic import Field, model_validator

from app.models.enums import StatusReserva
from app.schemas.comuns import SchemaBase


class ReservaEntrada(SchemaBase):
    espaco_id: int
    data: date
    hora_inicio: time
    hora_fim: time
    pessoas_estimadas: int | None = Field(default=None, ge=1, le=10000)
    observacoes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def conferir_intervalo(self) -> "ReservaEntrada":
        if self.hora_fim <= self.hora_inicio:
            raise ValueError("O horário de término precisa ser depois do início.")
        return self


class ReservaSaida(SchemaBase):
    """Resposta para o dono da reserva e para o síndico."""
    id: int
    espaco_id: int
    espaco_nome: str
    data: date
    hora_inicio: time
    hora_fim: time
    pessoas_estimadas: int | None = None
    observacoes: str | None = None
    status: StatusReserva
    motivo_recusa: str | None = None
    criado_em: datetime


class ReservaSindicoSaida(ReservaSaida):
    """Só o síndico vê quem reservou — ele é quem aprova (seção 13.5.3)."""
    morador_id: int
    morador_nome: str
    unidade: str | None = None


class OcupacaoAgenda(SchemaBase):
    """A agenda que o morador enxerga dos espaços.

    Mostra data e horário ocupados, sem nenhum dado de quem reservou:
    é o sigilo exigido pela seção 6.
    """
    espaco_id: int
    espaco_nome: str
    data: date
    hora_inicio: time
    hora_fim: time
    disponivel: bool = False


class AvaliacaoReserva(SchemaBase):
    """O síndico aprova ou recusa (seção 13.5.3)."""
    aprovada: bool
    motivo: str | None = Field(default=None, max_length=300)
