"""A cobrança cancelada não impede lançar a correta.

A restrição de uma cobrança por unidade e competência passa a ignorar as
canceladas: o síndico cancela a que saiu errada (ela fica guardada) e
lança a certa no mesmo mês.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-29 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_cobranca_competencia', 'cobrancas', type_='unique')
    op.create_index('uq_cobranca_competencia', 'cobrancas', ['unidade_id', 'competencia'],
                    unique=True, postgresql_where=sa.text("status <> 'CANCELADA'"))


def downgrade() -> None:
    op.drop_index('uq_cobranca_competencia', table_name='cobrancas')
    op.create_unique_constraint('uq_cobranca_competencia', 'cobrancas',
                                ['unidade_id', 'competencia'])
