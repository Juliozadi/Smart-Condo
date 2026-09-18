"""Configuração dos testes.

Os testes rodam contra um PostgreSQL de verdade (o mesmo banco da
documentação, seção 10.5), num schema recriado a cada sessão.
"""
from __future__ import annotations

import os

import pytest

# Definido antes de importar a aplicação, porque as settings são lidas na
# importação do módulo de configuração.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://smartcondo:smartcondo@127.0.0.1:5432/smartcondo_test",
)
os.environ.setdefault("SECRET_KEY", "chave-de-teste-suficientemente-longa")
os.environ.setdefault("DEBUG", "true")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

import app.models  # noqa: E402,F401  (registra as tabelas no metadata)
from app.core.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import app as aplicacao  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema_de_teste():
    with engine.begin() as conexao:
        conexao.execute(text("DROP SCHEMA public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def limpar_tabelas(schema_de_teste):
    """Cada teste começa com as tabelas vazias."""
    yield
    with engine.begin() as conexao:
        nomes = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        conexao.execute(text(f"TRUNCATE {nomes} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()


@pytest.fixture
def cliente():
    with TestClient(aplicacao) as c:
        yield c
