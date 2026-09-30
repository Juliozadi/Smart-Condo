"""Encomenda entregue em mãos na portaria.

Só o morador, pelo app, dava baixa na encomenda: entregue em mãos, ela
ficava "aguardando retirada" para sempre. O porteiro passa a registrar a
entrega, com quem entregou e o nome de quem levou.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-30 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('encomendas', sa.Column('entregue_por_id', sa.Integer(), nullable=True))
    op.add_column('encomendas', sa.Column('retirado_por_nome', sa.String(length=120),
                                          nullable=True))
    op.create_foreign_key('encomendas_entregue_por_id_fkey', 'encomendas', 'usuarios',
                          ['entregue_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('encomendas_entregue_por_id_fkey', 'encomendas', type_='foreignkey')
    op.drop_column('encomendas', 'retirado_por_nome')
    op.drop_column('encomendas', 'entregue_por_id')
