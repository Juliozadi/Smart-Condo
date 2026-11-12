"""Schemas do livro da portaria."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import Papel
from app.schemas.comuns import SchemaBase


class AnotacaoEntrada(SchemaBase):
    texto: str = Field(min_length=3, max_length=2000)
    importante: bool = False


class Ciencia(SchemaBase):
    nome: str
    em: datetime


class AnotacaoSaida(SchemaBase):
    id: int
    autor_nome: str | None = None
    autor_papel: Papel | None = None
    texto: str
    importante: bool
    criado_em: datetime
    cientes: list[Ciencia] = []
    # Importante, de outra pessoa, recente e ainda sem a minha ciência.
    preciso_ler: bool = False


class Pendentes(SchemaBase):
    total: int
