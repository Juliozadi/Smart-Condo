"""Schemas da portaria: visitantes, encomendas e ocorrências.

Documentação, seção 6 (História do Usuário) e seção 8.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.models.enums import (
    PrioridadeOcorrencia, StatusEncomenda, StatusOcorrencia, StatusVisitante,
)
from app.core.tempo import hoje_local
from app.schemas.comuns import CPF, Placa, SchemaBase


def _vazio_e_nada(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


# ── Autorização prévia de visita ─────────────────────────────────────
# Até um ano: cobre a diarista fixa e a obra longa; depois, renova.
PERIODO_MAXIMO_AUTORIZACAO = timedelta(days=365)


class AutorizacaoEntrada(SchemaBase):
    nome: str = Field(min_length=3, max_length=160)
    documento: CPF | None = None
    tipo: str = Field(min_length=3, max_length=60)
    valida_de: date
    valida_ate: date
    # 1 = segunda ... 7 = domingo (ISO). Vazio: todos os dias do período.
    dias_semana: list[Annotated[int, Field(ge=1, le=7)]] | None = Field(
        default=None, max_length=7)
    observacao: str | None = Field(default=None, max_length=300)
    # Pode levar a chave do apartamento deixada na portaria.
    pode_retirar_chave: bool = False

    _vazios = field_validator("documento", "observacao", mode="before")(_vazio_e_nada)

    @field_validator("dias_semana")
    @classmethod
    def _dias_sem_repeticao(cls, dias):
        if not dias:
            return None
        return sorted(set(dias))

    @model_validator(mode="after")
    def _periodo(self):
        hoje = hoje_local()
        if self.valida_de < hoje:
            raise ValueError("A autorização não pode começar numa data passada.")
        if self.valida_ate < self.valida_de:
            raise ValueError("A data final não pode ser antes da data inicial.")
        if self.valida_de > hoje + PERIODO_MAXIMO_AUTORIZACAO:
            raise ValueError("A autorização pode começar em até um ano.")
        if self.valida_ate - self.valida_de > PERIODO_MAXIMO_AUTORIZACAO:
            raise ValueError("A autorização vale por no máximo um ano; depois, renove.")
        if self.pode_retirar_chave and not self.documento:
            raise ValueError("Para retirar a chave, informe o CPF: a portaria confere o documento.")
        return self


class AutorizacaoSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str
    nome: str
    documento: str | None = None
    tipo: str
    valida_de: date
    valida_ate: date
    dias_semana: list[int] | None = None
    observacao: str | None = None
    pode_retirar_chave: bool = False
    autorizado_por_nome: str | None = None
    # Se a portaria pode registrar a entrada hoje, e se a pessoa já entrou
    # (e ainda não saiu) por esta autorização.
    vale_hoje: bool
    ja_dentro: bool = False
    criado_em: datetime


# ── Visitantes ───────────────────────────────────────────────────────
class VisitanteEntrada(SchemaBase):
    unidade_id: int
    nome: str = Field(min_length=3, max_length=160)
    documento: CPF
    tipo_visita: str = Field(min_length=3, max_length=60)
    # Normalizada como a do pátio (ABC1D23); em branco é "sem veículo".
    placa_veiculo: Placa | None = None
    # Entrada pela autorização prévia do morador: a pessoa entra sem
    # esperar resposta (o nome é o que o morador autorizou).
    autorizacao_id: int | None = None

    _placa_vazia = field_validator("placa_veiculo", mode="before")(_vazio_e_nada)

    # A foto do vídeo porteiro (seção 6) não vem aqui: ela é enviada como
    # arquivo em PUT /portaria/visitantes/{id}/foto logo depois do registro.


class VisitanteSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    nome: str
    documento: str
    tipo_visita: str
    placa_veiculo: str | None = None
    # Caminho na API (/portaria/visitantes/{id}/foto), que só responde com
    # o token de quem pode ver. None quando não há foto.
    foto_url: str | None = None
    status: StatusVisitante
    entrada_em: datetime | None = None
    saida_em: datetime | None = None
    confirmado_em: datetime | None = None
    autorizacao_id: int | None = None
    criado_em: datetime
    # Na resposta do registro: ninguém mora no apartamento pelo sistema, e
    # quem foi avisado foi o síndico.
    sem_morador: bool = False


class ConfirmacaoVisitante(SchemaBase):
    """"o cliente confirme se é ou não seu convidado" (seção 6)."""
    confirmado: bool


# ── Encomendas ───────────────────────────────────────────────────────
class EncomendaEntrada(SchemaBase):
    unidade_id: int
    remetente: str = Field(min_length=2, max_length=120)
    tipo_volume: str = Field(min_length=2, max_length=60)
    codigo_rastreio: str | None = Field(default=None, max_length=60)
    observacoes: str | None = Field(default=None, max_length=500)
    # A foto do volume vai como arquivo, em PUT /portaria/encomendas/{id}/foto.


class EncomendaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    remetente: str
    tipo_volume: str
    codigo_rastreio: str | None = None
    observacoes: str | None = None
    # Caminho na API (/portaria/encomendas/{id}/foto), como no visitante.
    foto_url: str | None = None
    status: StatusEncomenda
    recebida_em: datetime
    retirada_em: datetime | None = None
    # Entregue em mãos na portaria: a quem e por quem.
    retirado_por_nome: str | None = None
    entregue_por_nome: str | None = None
    criado_em: datetime
    # Na resposta do registro, como no visitante.
    sem_morador: bool = False


class RetiradaEncomenda(SchemaBase):
    confirmada: bool


class EntregaEncomenda(SchemaBase):
    """O porteiro entrega em mãos e anota quem levou."""
    retirado_por_nome: str = Field(min_length=3, max_length=120)


# ── Ocorrências ──────────────────────────────────────────────────────
class OcorrenciaEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=5, max_length=4000)
    categoria: str = Field(default="geral", max_length=60)
    local: str | None = Field(default=None, max_length=120)
    prioridade: PrioridadeOcorrencia = PrioridadeOcorrencia.NORMAL
    # A foto vai como arquivo, em PUT /portaria/ocorrencias/{id}/foto.


class OcorrenciaSaida(SchemaBase):
    id: int
    titulo: str
    descricao: str
    categoria: str
    local: str | None = None
    prioridade: PrioridadeOcorrencia
    # Caminho na API (/portaria/ocorrencias/{id}/foto), que pede o token.
    foto_url: str | None = None
    status: StatusOcorrencia
    aberta_por_id: int
    aberta_por_nome: str
    unidade: str | None = None
    resposta: str | None = None
    respondida_em: datetime | None = None
    criado_em: datetime


class RespostaOcorrencia(SchemaBase):
    status: StatusOcorrencia
    resposta: str = Field(min_length=3, max_length=2000)
