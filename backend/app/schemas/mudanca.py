"""Schemas do agendamento de mudança."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import StatusMudanca, TipoMudanca
from app.schemas.comuns import Horario, SchemaBase, conferir_intervalo, vazio_e_nada

# Até quando se agenda: mais que isso é engano na data.
ANTECEDENCIA_MAXIMA_DIAS = 365


class MudancaEntrada(SchemaBase):
    tipo: TipoMudanca
    data: date
    hora_inicio: Horario
    hora_fim: Horario
    empresa: str | None = Field(default=None, max_length=120)
    observacao: str | None = Field(default=None, max_length=300)

    @field_validator("data")
    @classmethod
    def nao_muito_longe(cls, valor: date) -> date:
        if valor > hoje_local() + timedelta(days=ANTECEDENCIA_MAXIMA_DIAS):
            raise ValueError("A mudança pode ser agendada com até um ano de antecedência.")
        return valor

    _vazios = field_validator("empresa", "observacao", mode="before")(vazio_e_nada)

    @model_validator(mode="after")
    def _intervalo(self) -> "MudancaEntrada":
        conferir_intervalo(self.hora_inicio, self.hora_fim)
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
    inicio: Horario
    fim: Horario


class RegrasMudancaEntrada(SchemaBase):
    """O regimento do condomínio: aviso mínimo e, para cada dia da semana
    em que pode haver mudança, o horário. Dia que não vem não tem mudança."""
    antecedencia_minima_dias: int = Field(ge=0, le=60)
    horarios: dict[int, HorarioDoDia]

    @field_validator("horarios")
    @classmethod
    def conferir_dias(cls, horarios: dict[int, HorarioDoDia]) -> dict[int, HorarioDoDia]:
        if not horarios:
            raise ValueError("Escolha pelo menos um dia da semana para as mudanças.")
        for dia, h in horarios.items():
            if not 1 <= dia <= 7:
                raise ValueError("Os dias da semana vão de 1 (segunda) a 7 (domingo).")
            if h.fim <= h.inicio:
                raise ValueError("Em cada dia, o fim do horário precisa ser depois do início.")
        return horarios


class RegrasMudanca(SchemaBase):
    antecedencia_minima_dias: int
    antecedencia_maxima_dias: int
    # Dia da semana (1 = segunda ... 7 = domingo) → horário permitido;
    # o dia que não aparece não tem mudança.
    horarios: dict[int, HorarioDoDia]
