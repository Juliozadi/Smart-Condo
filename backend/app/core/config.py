"""Configuração da aplicação, lida do ambiente (.env)."""
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CHAVE_DE_EXEMPLO = "troque-esta-chave-em-producao"


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
    SECRET_KEY: str = Field(default=CHAVE_DE_EXEMPLO, min_length=16)
    ALGORITMO_JWT: str = "HS256"
    ACCESS_TOKEN_EXPIRA_MIN: int = 60 * 8

    # Custo do bcrypt. 12 e o padrao seguro; os testes baixam para 4 para
    # nao gastar segundos por hash.
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=16)

    # Validade do código de confirmação de cadastro e de recuperação de
    # senha (documentação, seção 9: "Cadastro" e "Esqueci minha senha").
    CODIGO_VERIFICACAO_EXPIRA_MIN: int = 15

    # ── CORS ─────────────────────────────────────────────────────────
    # O front-end é servido de qualquer porta local (o python -m
    # http.server, o Live Server do VS Code, etc.), então a origem é
    # liberada por expressão em vez de uma lista fixa de portas — senão
    # o navegador bloqueia o login com "não foi possível falar com o
    # servidor". Em produção, aponte CORS_ORIGINS para o domínio real.
    CORS_ORIGINS: list[str] = []
    CORS_ORIGIN_REGEX: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    @model_validator(mode="after")
    def _recusar_chave_de_exemplo(self) -> "Settings":
        """Com DEBUG desligado, subir com a chave do .env.example seria
        deixar qualquer um assinar um token: ela está no repositório, e
        é ela que assina o JWT e embaralha os códigos de verificação.
        """
        if not self.DEBUG and self.SECRET_KEY == CHAVE_DE_EXEMPLO:
            raise ValueError(
                "SECRET_KEY ainda é a de exemplo.\n"
                "  Primeira vez aqui? Copie backend/.env.example para "
                "backend/.env — ele já vem com DEBUG=true.\n"
                "  Em produção, gere uma chave própria com:\n"
                "    python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
