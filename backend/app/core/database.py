"""Sessão e base declarativa do SQLAlchemy."""
from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pre_carregar(db: Session, modelo, ids) -> list:
    """Traz de uma vez os registros com esses ids.

    Quem chama guarda a lista enquanto monta a resposta: a sessão só
    lembra de um objeto enquanto alguém o referencia, e aí cada db.get da
    listagem o acha na memória. Sem isso, uma lista de 300 reservas fazia
    300 consultas, uma por unidade, mesmo com as unidades se repetindo.
    """
    ids = {i for i in ids if i is not None}
    if not ids:
        return []
    return list(db.scalars(select(modelo).where(modelo.id.in_(ids))).all())
