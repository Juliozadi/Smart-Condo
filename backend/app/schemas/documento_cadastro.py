"""Documentos enviados pelo morador no cadastro."""
from __future__ import annotations

from datetime import datetime

from app.models.enums import TipoDocumentoCadastro
from app.schemas.comuns import SchemaBase


class DocumentoCadastroSaida(SchemaBase):
    id: int
    tipo: TipoDocumentoCadastro
    tipo_conteudo: str
    tamanho_bytes: int
    enviado_em: datetime
    # Caminho na API para abrir o arquivo; só o síndico do condomínio
    # consegue (com o token dele).
    url: str
