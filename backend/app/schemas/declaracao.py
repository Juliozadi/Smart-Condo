"""Schemas da declaração de quitação."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.comuns import SchemaBase

Situacao = Literal["valida", "vencida", "revogada"]


class DeclaracaoEntrada(SchemaBase):
    # O morador emite a do próprio apartamento; o síndico escolhe qual.
    unidade_id: int | None = Field(default=None, ge=1)


class RevogacaoEntrada(SchemaBase):
    motivo: str = Field(min_length=5, max_length=500)


class DeclaracaoSaida(SchemaBase):
    id: int
    codigo: str
    unidade: str
    referencia_ate: date
    valida_ate: date
    emitida_em: datetime
    situacao: Situacao
    # Só para o síndico: o morador não vê quem pediu antes dele.
    emitida_por_nome: str | None = None
    revogada_em: datetime | None = None
    motivo_revogacao: str | None = None
    pode_revogar: bool = False


class DeclaracaoPublica(SchemaBase):
    """O que qualquer um vê com o código: o documento, sem dado pessoal
    de quem pediu e sem o motivo de uma revogação."""
    codigo: str
    condominio_nome: str
    condominio_cnpj: str
    unidade: str
    sindico_nome: str | None = None
    referencia_ate: date
    valida_ate: date
    emitida_em: datetime
    situacao: Situacao
    revogada_em: datetime | None = None
