"""SmartCondo — API.

Sistema de Gerenciamento de Condomínios (Projeto Integrador I).
Documentação, seção 10.4: o back-end é em Python; seção 10.5: PostgreSQL.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import auth, condominios, reservas, usuarios
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
)

app = FastAPI(
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(condominios.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(reservas.router, prefix="/api/v1")


@app.get("/api/v1/saude", tags=["Serviço"], summary="Verificação de disponibilidade")
def saude() -> dict[str, str]:
    return {"status": "ok", "aplicacao": settings.APP_NOME, "versao": settings.APP_VERSAO}
