"""Fração ideal das unidades e cota extra.

unidades ganha fracao_ideal (em porcentagem, como na convenção), por onde
se rateiam a taxa e as cotas extras; origem_cobranca ganha EXTRA, a cota
extra (chamada de capital) que a assembleia aprovou.

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-11-11 00:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORIGENS_ANTIGAS = "'TAXA', 'MULTA', 'USO_ESPACO', 'ACORDO'"
INDICE_TAXA = ("CREATE UNIQUE INDEX uq_cobranca_competencia ON cobrancas "
               "(unidade_id, competencia) "
               "WHERE status <> 'CANCELADA' AND origem = 'TAXA'")


def upgrade() -> None:
    op.execute("ALTER TYPE origem_cobranca ADD VALUE IF NOT EXISTS 'EXTRA'")
    op.add_column('unidades', sa.Column('fracao_ideal', sa.Numeric(precision=7, scale=4),
                                        nullable=True))
    op.create_check_constraint(
        'ck_unidade_fracao_ideal', 'unidades',
        'fracao_ideal IS NULL OR (fracao_ideal > 0 AND fracao_ideal <= 100)')


def downgrade() -> None:
    op.drop_constraint('ck_unidade_fracao_ideal', 'unidades', type_='check')
    op.drop_column('unidades', 'fracao_ideal')
    # Sem cota extra, as cobranças dela saem; o PostgreSQL não remove valor
    # de enum, então o tipo é recriado sem ele.
    op.execute("DELETE FROM cobrancas WHERE origem = 'EXTRA'")
    op.execute("DROP INDEX uq_cobranca_competencia")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem DROP DEFAULT")
    op.execute("ALTER TYPE origem_cobranca RENAME TO origem_cobranca_antigo")
    op.execute(f"CREATE TYPE origem_cobranca AS ENUM ({ORIGENS_ANTIGAS})")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem TYPE origem_cobranca "
               "USING origem::text::origem_cobranca")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem SET DEFAULT 'TAXA'")
    op.execute("DROP TYPE origem_cobranca_antigo")
    op.execute(INDICE_TAXA)
