"""Tamanho máximo do corpo do pedido.

O FastAPI lê o corpo inteiro antes de conferir o login e antes de a rota
olhar o tamanho do arquivo. Sem um teto aqui, um corpo de gigabytes
mandado a qualquer rota — inclusive o /auth/login, que não pede conta —
ia todo para a memória (JSON) ou para o disco (arquivo), e poucos
pedidos assim derrubavam a API.

O limite vale com ou sem Content-Length: os bytes são contados à medida
que chegam. A recusa é uma HTTPException levantada na leitura, dentro da
rota, e por isso volta pelo tratador de erros com a resposta em JSON e
com o cabeçalho do CORS, como qualquer outro erro.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.core.config import settings

# Campos do formulário além do arquivo (título, descrição...) e as
# fronteiras do multipart.
FOLGA_MULTIPART_KB = 128

MENSAGEM = "O pedido é grande demais."


def _limite(scope) -> int:
    for nome, valor in scope.get("headers", ()):
        if nome == b"content-type" and valor.lower().startswith(b"multipart/"):
            maior = max(settings.FOTO_MAX_KB, settings.DOCUMENTO_MAX_KB)
            return (maior + FOLGA_MULTIPART_KB) * 1024
    return settings.CORPO_MAX_KB * 1024


def _declarado(scope) -> int | None:
    for nome, valor in scope.get("headers", ()):
        if nome == b"content-length":
            try:
                return int(valor)
            except ValueError:
                return None
    return None


class LimiteDeCorpo:
    """Middleware ASGI: recusa com 413 o corpo acima do limite."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limite = _limite(scope)
        declarado = _declarado(scope)
        recebido = 0

        async def receber():
            nonlocal recebido
            # Tamanho declarado acima do limite: recusa sem ler nada.
            if declarado is not None and declarado > limite:
                raise HTTPException(
                    status_code=413, detail=MENSAGEM
                )
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebido += len(mensagem.get("body", b""))
                if recebido > limite:
                    raise HTTPException(
                        status_code=413, detail=MENSAGEM
                    )
            return mensagem

        await self.app(scope, receber, send)
