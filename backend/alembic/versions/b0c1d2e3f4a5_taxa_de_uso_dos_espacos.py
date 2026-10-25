"""Taxa de uso dos espaços.

espacos_comuns.taxa_uso (vazia, sem taxa) e reservas.cobranca_id: a
taxa entra nas cobranças do apartamento quando o síndico aprova a
reserva, e sai se a reserva for cancelada antes de paga.

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-10-25 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b0c1d2e3f4a5'
down_revision: Union[str, None] = 'a9b0c1d2e3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('espacos_comuns', sa.Column('taxa_uso', sa.Numeric(precision=10, scale=2),
                                              nullable=True))
    op.create_check_constraint('ck_espaco_taxa_uso', 'espacos_comuns',
                               'taxa_uso IS NULL OR taxa_uso > 0')
    op.add_column('reservas', sa.Column('cobranca_id', sa.Integer(), nullable=True))
    op.create_foreign_key('reservas_cobranca_id_fkey', 'reservas', 'cobrancas',
                          ['cobranca_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('reservas_cobranca_id_fkey', 'reservas', type_='foreignkey')
    op.drop_column('reservas', 'cobranca_id')
    op.drop_constraint('ck_espaco_taxa_uso', 'espacos_comuns', type_='check')
    op.drop_column('espacos_comuns', 'taxa_uso')
