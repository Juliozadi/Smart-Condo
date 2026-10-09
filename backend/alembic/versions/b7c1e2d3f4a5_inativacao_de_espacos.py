"""Espaços comuns também são inativados, não apagados.

O síndico passa a cadastrar, editar, inativar e reativar os espaços pela
tela; antes só a carga de demonstração criava espaços.

Revision ID: b7c1e2d3f4a5
Revises: 6689b8d7c72f
Create Date: 2026-09-28 18:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c1e2d3f4a5'
down_revision: Union[str, None] = '6689b8d7c72f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('espacos_comuns',
                  sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True))
    op.add_column('espacos_comuns', sa.Column('inativado_por_id', sa.Integer(), nullable=True))
    op.create_foreign_key('espacos_comuns_inativado_por_id_fkey', 'espacos_comuns', 'usuarios',
                          ['inativado_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('espacos_comuns_inativado_por_id_fkey', 'espacos_comuns',
                       type_='foreignkey')
    op.drop_column('espacos_comuns', 'inativado_por_id')
    op.drop_column('espacos_comuns', 'inativo_em')
