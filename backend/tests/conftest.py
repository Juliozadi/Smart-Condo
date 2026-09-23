"""Configuração dos testes.

Os testes rodam contra um PostgreSQL de verdade (o mesmo banco da
documentação, seção 19.5), num schema recriado a cada sessão.
"""
from __future__ import annotations

import os

import pytest

# Definido antes de importar a aplicação, porque as settings são lidas na
# importação do módulo de configuração.
#
# A URL é FORÇADA, não um valor padrão. Com setdefault, quem tivesse
# DATABASE_URL exportada no terminal rodaria a suíte contra o próprio
# banco — e a primeira coisa que ela faz é DROP SCHEMA public CASCADE.
# Para apontar para outro banco de teste, use TEST_DATABASE_URL.
URL_DO_TESTE = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://smartcondo:smartcondo@127.0.0.1:5432/smartcondo_test",
)
if "test" not in URL_DO_TESTE.rsplit("/", 1)[-1]:
    raise SystemExit(
        "Recusando rodar: o nome do banco em TEST_DATABASE_URL precisa "
        f"conter 'test', senão a suíte apaga o schema dele.\n  {URL_DO_TESTE}"
    )
os.environ["DATABASE_URL"] = URL_DO_TESTE
os.environ.setdefault("SECRET_KEY", "chave-de-teste-suficientemente-longa")
os.environ.setdefault("DEBUG", "true")
# Custo minimo do bcrypt: os testes exercitam a regra, nao a forca do hash.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

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


@pytest.fixture(autouse=True)
def uploads_temporarios(tmp_path, monkeypatch):
    """Nenhum teste grava em backend/uploads, que é a pasta de verdade."""
    from app.core.config import settings

    pasta = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOADS_DIR", str(pasta))
    return pasta


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
