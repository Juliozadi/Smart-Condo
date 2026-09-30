"""Visitante sem resposta do morador.

O visitante que o morador não confirma nem recusa em 2 horas passa a "sem
resposta": antes ficava "aguardando" para sempre no painel da portaria, e
o morador podia confirmá-lo dias depois, registrando a entrada na hora.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-30 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANTIGOS = "'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'RECUSADO', 'DENTRO', 'SAIU'"


def upgrade() -> None:
    op.execute("ALTER TYPE status_visitante ADD VALUE IF NOT EXISTS 'SEM_RESPOSTA'")


def downgrade() -> None:
    # O PostgreSQL não remove valor de enum: recria o tipo sem ele.
    op.execute("UPDATE visitantes SET status = 'RECUSADO' WHERE status = 'SEM_RESPOSTA'")
    op.execute("ALTER TYPE status_visitante RENAME TO status_visitante_antigo")
    op.execute(f"CREATE TYPE status_visitante AS ENUM ({ANTIGOS})")
    op.execute("ALTER TABLE visitantes ALTER COLUMN status TYPE status_visitante "
               "USING status::text::status_visitante")
    op.execute("DROP TYPE status_visitante_antigo")
