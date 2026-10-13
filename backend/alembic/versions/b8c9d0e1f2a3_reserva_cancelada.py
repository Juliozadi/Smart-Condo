"""Quem cancelou a reserva, quando e por quê.

O síndico passa a cancelar a reserva já aprovada (vazamento no salão,
obra, evento do condomínio), com um motivo que vai para o morador. A
reserva guarda quem cancelou, quando e o motivo.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-10-13 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reservas', sa.Column('cancelada_por_id', sa.Integer(), nullable=True))
    op.add_column('reservas', sa.Column('cancelada_em', sa.DateTime(timezone=True),
                                        nullable=True))
    op.add_column('reservas', sa.Column('motivo_cancelamento', sa.Text(), nullable=True))
    op.create_foreign_key('reservas_cancelada_por_id_fkey', 'reservas', 'usuarios',
                          ['cancelada_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('reservas_cancelada_por_id_fkey', 'reservas', type_='foreignkey')
    op.drop_column('reservas', 'motivo_cancelamento')
    op.drop_column('reservas', 'cancelada_em')
    op.drop_column('reservas', 'cancelada_por_id')
