"""Schemas do chat (seção 13.5.2)."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import Papel
from app.schemas.comuns import SchemaBase


class MensagemEntrada(SchemaBase):
    texto: str = Field(min_length=1, max_length=2000)

    @field_validator("texto")
    @classmethod
    def _nao_vazia(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("A mensagem está vazia.")
        return valor


class MensagemSaida(SchemaBase):
    id: int
    remetente_id: int
    destinatario_id: int
    texto: str
    enviada_em: datetime
    lida_em: datetime | None = None
    minha: bool = False


class ContatoSaida(SchemaBase):
    """Uma pessoa com quem o usuário pode conversar, e o resumo da conversa."""
    id: int
    nome: str
    papel: Papel
    telefone: str
    foto_url: str | None = None
    unidade: str | None = None
    nao_lidas: int = 0
    ultima_mensagem: str | None = None
    ultima_em: datetime | None = None


class NaoLidasSaida(SchemaBase):
    total: int
