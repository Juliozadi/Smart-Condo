"""Configuração da aplicação, lida do ambiente (.env)."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Aplicação ────────────────────────────────────────────────────
    APP_NOME: str = "SmartCondo API"
    APP_VERSAO: str = "0.1.0"
    DEBUG: bool = False

    # ── Banco de dados (documentação, seção 10.5: PostgreSQL) ────────
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://smartcondo:smartcondo@localhost:5432/smartcondo",
        description="URL de conexão do PostgreSQL.",
    )

    # ── Autenticação ─────────────────────────────────────────────────
    # Em produção esta chave vem do ambiente; nunca deve ficar no código.
    SECRET_KEY: str = Field(default="troque-esta-chave-em-producao", min_length=16)
    ALGORITMO_JWT: str = "HS256"
    ACCESS_TOKEN_EXPIRA_MIN: int = 60 * 8

    # Validade do código de confirmação de cadastro e de recuperação de
    # senha (documentação, seção 9: "Cadastro" e "Esqueci minha senha").
    CODIGO_VERIFICACAO_EXPIRA_MIN: int = 15

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:8099", "http://127.0.0.1:8099"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
