"""SmartCondo — API.

Sistema de Gerenciamento de Condomínios (Projeto Integrador I).
Documentação, seção 19.4: o back-end é em Python; seção 19.5: PostgreSQL.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import (
    admin, arquivos, auth, comunicados, condominios, documentos, financeiro, manutencao,
    mensagens,
    portaria, reservas, usuarios, veiculos,
)
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
)

logger = logging.getLogger("smartcondo")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Avisa, ao subir, o que está faltando para o sistema funcionar.

    Sem SMTP o código de confirmação não chega a ninguém, e o morador
    que se cadastra fica preso em "aguardando código" sem entender por
    quê. Em desenvolvimento isso é esperado — o código volta na resposta
    da API. Em produção é uma falha silenciosa, então ela grita aqui.
    """
    if not settings.DEBUG and not settings.email_configurado:
        logger.warning(
            "SMTP não configurado: nenhum código de confirmação ou de "
            "recuperação de senha será entregue, e o cadastro de morador "
            "vai travar. Preencha SMTP_HOST no .env."
        )
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title=settings.APP_NOME,
    version=settings.APP_VERSAO,
    description=(
        "API do SmartCondo, o Sistema de Gerenciamento de Condomínios.\n\n"
        "Os endpoints seguem os casos de uso e as histórias de usuário "
        "descritos na documentação do projeto."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Com DEBUG ligado o index.html aberto direto do disco (file://) também
# é aceito: o navegador manda a origem "null" nesse caso.
_origens = list(settings.CORS_ORIGINS)
if settings.DEBUG:
    _origens.append("null")

# Registrado antes do CORS de propósito: o middleware adicionado antes
# fica por dentro na pilha, e só assim o CORS enxerga esta resposta para
# carimbar o cabeçalho de origem. O tratador @app.exception_handler não
# serviria: ele roda por fora de todos os middlewares.
@app.middleware("http")
async def erro_inesperado(requisicao: Request, proxima):
    """Transforma a exceção não prevista numa resposta JSON.

    Sem isto, a exceção escapa até o Starlette, que responde 500 em
    texto puro e sem CORS. O navegador descarta o corpo e a tela mostra
    "não foi possível falar com o servidor" — a mesma mensagem de quando
    a API está desligada. Quem estivesse só com o banco parado
    procuraria o problema no lugar errado.

    O motivo real vai para o diário do servidor, não para a resposta:
    mensagem de exceção costuma revelar caminho de arquivo, nome de
    tabela e trecho de consulta.
    """
    try:
        return await proxima(requisicao)
    except Exception:  # noqa: BLE001 — qualquer falha não prevista
        logger.exception(
            "Erro não tratado em %s %s", requisicao.method, requisicao.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detalhe": "Erro interno no servidor. Tente novamente em instantes."},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cabeçalhos de segurança ──────────────────────────────────────────
# A API devolve JSON e nada mais. Estes cabeçalhos custam nada e fecham
# portas que o navegador deixaria abertas por padrão.
@app.middleware("http")
async def cabecalhos_de_seguranca(requisicao: Request, proxima):
    resposta = await proxima(requisicao)
    # Não deixa o navegador adivinhar o tipo do conteúdo.
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    # A API não é para ser exibida dentro de um iframe de ninguém.
    resposta.headers["X-Frame-Options"] = "DENY"
    # Não vaza a URL da API ao seguir um link para fora.
    resposta.headers["Referrer-Policy"] = "no-referrer"
    # Uma resposta JSON não carrega script, imagem nem estilo. As páginas
    # /docs e /redoc são a exceção: elas montam a interface do Swagger
    # com arquivos de CDN e quebrariam com esta política.
    if not requisicao.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        resposta.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    # Só vale sobre HTTPS; o navegador ignora quando vem por HTTP.
    if not settings.DEBUG:
        resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resposta


# ── Erros em português ───────────────────────────────────────────────
# O FastAPI responde com a chave "detail"; a API do SmartCondo padroniza
# "detalhe", que é o que os schemas de sucesso também usam.
@app.exception_handler(StarletteHTTPException)
async def erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detalhe": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detalhe": "Há campos inválidos na requisição.",
            "campos": jsonable_encoder(exc.errors()),
        },
    )



app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(condominios.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(reservas.router, prefix="/api/v1")
app.include_router(portaria.router, prefix="/api/v1")
app.include_router(financeiro.router, prefix="/api/v1")
app.include_router(comunicados.router, prefix="/api/v1")
app.include_router(veiculos.router, prefix="/api/v1")
app.include_router(manutencao.router, prefix="/api/v1")
app.include_router(documentos.router, prefix="/api/v1")
app.include_router(arquivos.router, prefix="/api/v1")
app.include_router(mensagens.router, prefix="/api/v1")


@app.get("/api/v1/saude", tags=["Serviço"], summary="Verificação de disponibilidade")
def saude() -> dict[str, str]:
    return {"status": "ok", "aplicacao": settings.APP_NOME, "versao": settings.APP_VERSAO}
