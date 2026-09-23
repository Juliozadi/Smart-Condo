"""Gravação e entrega das fotos de perfil.

Quem decide o tipo do arquivo são os primeiros bytes dele, não a
extensão nem o Content-Type que o navegador informa: os dois são
escolhidos por quem envia. Um .jpg que na verdade é um HTML seria
servido de volta a outros usuários; conferindo a assinatura, só entra
JPEG, PNG ou WebP de verdade.

O nome gravado é aleatório. Ele é a única coisa que dá acesso à foto
(a tag <img> não manda o token de sessão), então precisa ser impossível
de adivinhar — e nunca vem de nada que o usuário escreveu, o que também
fecha a porta para nomes como "../../app/main.py".
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path

from app.core.config import settings

# Assinatura no começo do arquivo → extensão gravada.
_ASSINATURAS = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)
TIPOS = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
PREFIXO_URL = "/arquivos/fotos/"
NOME_VALIDO = re.compile(r"^[A-Za-z0-9_-]{20,64}\.(jpg|png|webp)$")


class ArquivoRecusado(ValueError):
    """O conteúdo enviado não pode virar foto de perfil."""


def pasta_de_fotos() -> Path:
    base = Path(settings.UPLOADS_DIR)
    if not base.is_absolute():
        base = Path(__file__).resolve().parents[2] / base
    pasta = base / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def tipo_da_imagem(conteudo: bytes) -> str | None:
    for assinatura, extensao in _ASSINATURAS:
        if conteudo.startswith(assinatura):
            return extensao
    if len(conteudo) >= 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp"
    return None


def salvar_foto(conteudo: bytes) -> str:
    """Grava a foto e devolve o caminho que vai para foto_url."""
    if not conteudo:
        raise ArquivoRecusado("O arquivo está vazio.")
    if len(conteudo) > settings.FOTO_MAX_KB * 1024:
        raise ArquivoRecusado(
            f"A foto passa de {settings.FOTO_MAX_KB // 1024 or 1} MB. Envie uma imagem menor."
        )
    extensao = tipo_da_imagem(conteudo)
    if extensao is None:
        raise ArquivoRecusado("Envie uma imagem JPG, PNG ou WebP.")
    nome = f"{secrets.token_urlsafe(24)}.{extensao}"
    (pasta_de_fotos() / nome).write_bytes(conteudo)
    return PREFIXO_URL + nome


def caminho_da_foto(nome: str) -> Path | None:
    """O arquivo correspondente a um nome pedido, se ele for válido e existir."""
    if not NOME_VALIDO.match(nome):
        return None
    caminho = pasta_de_fotos() / nome
    return caminho if caminho.is_file() else None


def apagar_foto(foto_url: str | None) -> None:
    """Remove do disco a foto anterior, quando ela foi enviada por aqui."""
    if not foto_url or not foto_url.startswith(PREFIXO_URL):
        return
    caminho = caminho_da_foto(foto_url[len(PREFIXO_URL):])
    if caminho is not None:
        caminho.unlink(missing_ok=True)
