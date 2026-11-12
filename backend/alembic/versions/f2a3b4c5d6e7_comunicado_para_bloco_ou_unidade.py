"""Comunicado para um bloco ou para um apartamento.

"Falta de água no bloco B" só interessa ao bloco B; a advertência por
barulho é do apartamento, e não da conta dos vizinhos. Os dois vazios:
o condomínio inteiro, como os comunicados que já existem.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-10-14 02:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('comunicados', sa.Column('bloco', sa.String(length=20), nullable=True))
    op.add_column('comunicados', sa.Column('unidade_id', sa.Integer(), nullable=True))
    op.create_foreign_key('comunicados_unidade_id_fkey', 'comunicados', 'unidades',
                          ['unidade_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_comunicados_unidade_id'), 'comunicados', ['unidade_id'])
    op.create_check_constraint('ck_comunicado_um_destino', 'comunicados',
                               'bloco IS NULL OR unidade_id IS NULL')


def downgrade() -> None:
    op.drop_constraint('ck_comunicado_um_destino', 'comunicados', type_='check')
    op.drop_index(op.f('ix_comunicados_unidade_id'), table_name='comunicados')
    op.drop_constraint('comunicados_unidade_id_fkey', 'comunicados', type_='foreignkey')
    op.drop_column('comunicados', 'unidade_id')
    op.drop_column('comunicados', 'bloco')
