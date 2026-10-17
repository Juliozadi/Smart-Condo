"""Schemas dos comunicados (documentação, seção 13.5.4 e 13.6.4)."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.models.enums import CategoriaComunicado
from app.schemas.comuns import IdUnidade, SchemaBase


class ComunicadoEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    conteudo: str = Field(min_length=5, max_length=8000)
    categoria: CategoriaComunicado = CategoriaComunicado.GERAL
    fixado: bool = False
    # Vazios: o condomínio inteiro. Um ou outro, nunca os dois.
    bloco: IdUnidade | None = Field(default=None, max_length=20)
    unidade_id: int | None = None

    @field_validator("bloco", mode="before")
    @classmethod
    def _bloco_vazio(cls, valor):
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @model_validator(mode="after")
    def _um_destino(self):
        if self.bloco is not None and self.unidade_id is not None:
            raise ValueError("Escolha um bloco ou um apartamento, não os dois.")
        return self


class ComunicadoSaida(SchemaBase):
    id: int
    titulo: str
    conteudo: str
    categoria: CategoriaComunicado
    fixado: bool
    publicado_em: datetime
    autor_nome: str
    lido: bool = False
    bloco: str | None = None
    unidade_id: int | None = None
    # "Todo o condomínio", "Bloco B" ou "Apto B 101".
    destino: str = "Todo o condomínio"
