"""Animais de estimação: o que entra e o que sai da API."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from pydantic import Field, field_validator, model_validator

from app.core.tempo import hoje_local
from app.models.enums import EspecieAnimal, PorteAnimal
from app.schemas.comuns import SchemaBase, vazio_e_nada

# A antirrábica vale um ano: mais que isso à frente é data digitada errada.
VALIDADE_MAXIMA_DIAS = 400
OPCIONAIS = ("raca", "cor", "observacao")


def _conferir_vacina(valor: date | None) -> date | None:
    if valor is None:
        return None
    hoje = hoje_local()
    if valor > hoje + timedelta(days=VALIDADE_MAXIMA_DIAS):
        raise ValueError("A vacina antirrábica vale um ano: confira a data de validade.")
    if valor < hoje - timedelta(days=10 * 365):
        raise ValueError("Confira a data de validade da vacina.")
    return valor


class AnimalEntrada(SchemaBase):
    unidade_id: int | None = None  # só o síndico informa; o morador cadastra no dele
    nome: str = Field(min_length=1, max_length=60)
    especie: EspecieAnimal
    raca: str | None = Field(default=None, max_length=60)
    porte: PorteAnimal
    cor: str | None = Field(default=None, max_length=40)
    vacina_antirrabica_ate: date | None = None
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator(*OPCIONAIS, mode="before")(vazio_e_nada)
    _vacina = field_validator("vacina_antirrabica_ate")(_conferir_vacina)


class AnimalAtualizacao(SchemaBase):
    nome: str | None = Field(default=None, min_length=1, max_length=60)
    especie: EspecieAnimal | None = None
    raca: str | None = Field(default=None, max_length=60)
    porte: PorteAnimal | None = None
    cor: str | None = Field(default=None, max_length=40)
    vacina_antirrabica_ate: date | None = None
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator(*OPCIONAIS, mode="before")(vazio_e_nada)
    _vacina = field_validator("vacina_antirrabica_ate")(_conferir_vacina)

    @model_validator(mode="after")
    def _obrigatorios(self) -> "AnimalAtualizacao":
        # Nome, espécie e porte podem mudar, mas não ficar em branco.
        for campo in ("nome", "especie", "porte"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"Informe {campo}.")
        return self


class AnimalSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    nome: str
    especie: EspecieAnimal
    raca: str | None
    porte: PorteAnimal
    cor: str | None
    vacina_antirrabica_ate: date | None
    # em_dia, vencida (a data passou) ou sem_registro.
    vacina: str
    observacao: str | None
    cadastrado_por_nome: str | None
    lembrete_vacina_em: datetime | None = None
    pode_editar: bool


class LembreteSaida(SchemaBase):
    animais: int
    apartamentos: int
