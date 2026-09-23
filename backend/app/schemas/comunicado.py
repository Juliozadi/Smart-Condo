"""Schemas dos comunicados (documentação, seção 13.5.4 e 13.6.4)."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import CategoriaComunicado
from app.schemas.comuns import SchemaBase


class ComunicadoEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    conteudo: str = Field(min_length=5, max_length=8000)
    categoria: CategoriaComunicado = CategoriaComunicado.GERAL
    fixado: bool = False


class ComunicadoSaida(SchemaBase):
    id: int
    titulo: str
    conteudo: str
    categoria: CategoriaComunicado
    fixado: bool
    publicado_em: datetime
    autor_nome: str
    lido: bool = False
