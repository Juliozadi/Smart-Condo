"""Gravação dos arquivos enviados: fotos de perfil, fotos da portaria e
documentos do cadastro.

Quem decide o tipo do arquivo são os primeiros bytes dele, não a
extensão nem o Content-Type que o navegador informa: os dois são
escolhidos por quem envia. Um .jpg que na verdade é um HTML seria
servido de volta a outros usuários; conferindo a assinatura, só entra
JPEG, PNG ou WebP de verdade.

O nome gravado é aleatório. Ele é a única coisa que dá acesso à foto
(a tag <img> não manda o token de sessão), então precisa ser impossível
de adivinhar — e nunca vem de nada que o usuário escreveu, o que também
fecha a porta para nomes como "../../app/main.py".

As fotos de perfil ficam em uploads/fotos e são públicas por endereço.
As fotos de visitantes e encomendas e os documentos do cadastro são
dados pessoais de terceiros (LGPD): ficam em pastas próprias, que
nenhuma rota pública serve, e só saem por rotas que conferem o token e
quem tem direito a ver cada arquivo.
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
TIPOS = {
    "jpg": "image/jpeg", "png": "image/png", "webp": "image/webp",
    "pdf": "application/pdf",
}
PREFIXO_URL = "/arquivos/fotos/"
NOME_VALIDO = re.compile(r"^[A-Za-z0-9_-]{20,64}\.(jpg|png|webp)$")
NOME_PRIVADO_VALIDO = re.compile(r"^[A-Za-z0-9_-]{20,64}\.(jpg|png|webp|pdf)$")

# Pastas dos arquivos que só saem com autorização.
PORTARIA = "portaria"
OCORRENCIAS = "ocorrencias"
DOCUMENTOS = "documentos"
CONDOMINIO = "condominio"   # atas, convenção, regimento…
_PASTAS_PRIVADAS = {PORTARIA, OCORRENCIAS, DOCUMENTOS, CONDOMINIO}


class ArquivoRecusado(ValueError):
    """O conteúdo enviado não é aceito (vazio, grande demais ou de outro tipo)."""


def _pasta(nome: str) -> Path:
    base = Path(settings.UPLOADS_DIR)
    if not base.is_absolute():
        base = Path(__file__).resolve().parents[2] / base
    pasta = base / nome
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def pasta_de_fotos() -> Path:
    return _pasta("fotos")


def tipo_da_imagem(conteudo: bytes) -> str | None:
    for assinatura, extensao in _ASSINATURAS:
        if conteudo.startswith(assinatura):
            return extensao
    if len(conteudo) >= 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp"
    return None


def tipo_do_documento(conteudo: bytes) -> str | None:
    """Imagem ou PDF. Um PDF de verdade começa com "%PDF-"."""
    if conteudo.startswith(b"%PDF-"):
        return "pdf"
    return tipo_da_imagem(conteudo)


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


# ── Arquivos privados ────────────────────────────────────────────────
def salvar_privado(pasta: str, conteudo: bytes, *, aceita_pdf: bool, max_kb: int) -> str:
    """Grava o arquivo numa pasta privada e devolve só o nome gravado.

    O nome vai para o banco; o endereço de acesso é montado pela rota,
    que é quem confere a permissão.
    """
    if pasta not in _PASTAS_PRIVADAS:
        raise ValueError(f"Pasta privada desconhecida: {pasta}")
    if not conteudo:
        raise ArquivoRecusado("O arquivo está vazio.")
    if len(conteudo) > max_kb * 1024:
        raise ArquivoRecusado(
            f"O arquivo passa de {max_kb // 1024 or 1} MB. Envie um arquivo menor."
        )
    extensao = tipo_do_documento(conteudo) if aceita_pdf else tipo_da_imagem(conteudo)
    if extensao is None:
        raise ArquivoRecusado(
            "Envie um PDF ou uma imagem JPG, PNG ou WebP." if aceita_pdf
            else "Envie uma imagem JPG, PNG ou WebP."
        )
    nome = f"{secrets.token_urlsafe(24)}.{extensao}"
    (_pasta(pasta) / nome).write_bytes(conteudo)
    return nome


def caminho_privado(pasta: str, nome: str | None) -> Path | None:
    """O arquivo gravado com esse nome, se o nome for válido e o arquivo existir.

    Registros antigos podem ter no campo um endereço qualquer em vez de
    um nome gravado aqui; esses contam como "sem arquivo".
    """
    if pasta not in _PASTAS_PRIVADAS or not nome or not NOME_PRIVADO_VALIDO.match(nome):
        return None
    caminho = _pasta(pasta) / nome
    return caminho if caminho.is_file() else None


def apagar_privado(pasta: str, nome: str | None) -> None:
    caminho = caminho_privado(pasta, nome)
    if caminho is not None:
        caminho.unlink(missing_ok=True)


def tipo_de_conteudo(nome: str) -> str:
    return TIPOS[nome.rsplit(".", 1)[-1]]
