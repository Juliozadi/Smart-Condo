"""Schemas do controle de chaves."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.comuns import SchemaBase


def _vazio_e_nada(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


class ChaveEntrada(SchemaBase):
    nome: str = Field(min_length=3, max_length=80)
    # Vazio: chave de área comum.
    unidade_id: int | None = Field(default=None, ge=1)
    posicao: str | None = Field(default=None, max_length=20)
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("posicao", "observacao", mode="before")(_vazio_e_nada)


class ChaveAtualizacao(SchemaBase):
    """Só o que veio muda; a chave não troca de apartamento."""
    nome: str | None = Field(default=None, min_length=3, max_length=80)
    posicao: str | None = Field(default=None, max_length=20)
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("posicao", "observacao", mode="before")(_vazio_e_nada)


class ChaveSaida(SchemaBase):
    id: int
    nome: str
    unidade_id: int | None = None
    unidade: str | None = None
    posicao: str | None = None
    observacao: str | None = None
    na_portaria: bool
    # Com quem está, e desde quando, se saiu.
    com: str | None = None
    retirada_em: datetime | None = None


class RetiradaEntrada(SchemaBase):
    # Chave de área comum: o nome de quem leva. Chave de apartamento: um
    # morador de lá (morador_id) ou uma autorização dele (autorizacao_id),
    # com o documento que a pessoa apresentou.
    nome: str | None = Field(default=None, min_length=3, max_length=160)
    documento: str | None = Field(default=None, max_length=20)
    morador_id: int | None = Field(default=None, ge=1)
    autorizacao_id: int | None = Field(default=None, ge=1)
    observacao: str | None = Field(default=None, max_length=300)

    _vazios = field_validator("nome", "documento", "observacao", mode="before")(_vazio_e_nada)


class MovimentacaoSaida(SchemaBase):
    id: int
    retirada_por_nome: str
    retirada_por_documento: str | None = None
    retirada_em: datetime
    retirada_registrada_por_nome: str | None = None
    devolvida_em: datetime | None = None
    devolucao_registrada_por_nome: str | None = None
    observacao: str | None = None


class QuemPodeRetirar(SchemaBase):
    tipo: Literal["morador", "autorizacao"]
    id: int
    nome: str
    # Da autorização: o tipo (diarista, eletricista) e o meio do CPF.
    detalhe: str | None = None
    documento: str | None = None
