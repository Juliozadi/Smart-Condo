"""Objetos do banco: visões, funções, procedimentos, gatilhos e log das cobranças.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-11-12
"""
from alembic import op

from app.core.objetos_banco import CRIAR, REMOVER

revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def _executar(sql: str) -> None:
    # Pelo driver e sem parâmetros: o SQL tem vários comandos e o % dos
    # RAISE, que o SQLAlchemy trataria como marcador de parâmetro.
    op.get_bind().connection.driver_connection.execute(sql)


def upgrade() -> None:
    _executar(CRIAR)


def downgrade() -> None:
    _executar(REMOVER)
