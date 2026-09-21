"""Schemas da portaria: visitantes, encomendas e ocorrências.

Documentação, seção 6 (História do Usuário) e seção 8.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import (
    PrioridadeOcorrencia, StatusEncomenda, StatusOcorrencia, StatusVisitante,
)
from app.schemas.comuns import CPF, SchemaBase


# ── Visitantes ───────────────────────────────────────────────────────
class VisitanteEntrada(SchemaBase):
    unidade_id: int
    nome: str = Field(min_length=3, max_length=160)
    documento: CPF
    tipo_visita: str = Field(min_length=3, max_length=60)
    placa_veiculo: str | None = Field(default=None, max_length=10)
    # Vídeo porteiro: a foto capturada na portaria (seção 6).
    foto_url: str | None = Field(default=None, max_length=500)


class VisitanteSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    nome: str
    documento: str
    tipo_visita: str
    placa_veiculo: str | None = None
    foto_url: str | None = None
    status: StatusVisitante
    entrada_em: datetime | None = None
    saida_em: datetime | None = None
    confirmado_em: datetime | None = None
    criado_em: datetime


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
    # Foto do volume enviada ao morador junto da notificação (seção 6).
    foto_url: str | None = Field(default=None, max_length=500)


class EncomendaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    remetente: str
    tipo_volume: str
    codigo_rastreio: str | None = None
    observacoes: str | None = None
    foto_url: str | None = None
    status: StatusEncomenda
    recebida_em: datetime
    retirada_em: datetime | None = None
    criado_em: datetime


class RetiradaEncomenda(SchemaBase):
    confirmada: bool


# ── Ocorrências ──────────────────────────────────────────────────────
class OcorrenciaEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str = Field(min_length=5, max_length=4000)
    categoria: str = Field(default="geral", max_length=60)
    local: str | None = Field(default=None, max_length=120)
    prioridade: PrioridadeOcorrencia = PrioridadeOcorrencia.NORMAL
    foto_url: str | None = Field(default=None, max_length=500)


class OcorrenciaSaida(SchemaBase):
    id: int
    titulo: str
    descricao: str
    categoria: str
    local: str | None = None
    prioridade: PrioridadeOcorrencia
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
