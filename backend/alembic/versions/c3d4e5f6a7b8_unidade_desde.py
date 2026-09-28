"""Desde quando o usuário mora na unidade atual.

O morador vê os visitantes e as encomendas da unidade a partir de quando
passou a morar nela. Antes a referência era a data do cadastro, e o
morador transferido via o histórico de quem estava no apartamento novo.

Revision ID: c3d4e5f6a7b8
Revises: b7c1e2d3f4a5
Create Date: 2026-09-29 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b7c1e2d3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('unidade_desde', sa.DateTime(timezone=True),
                                        server_default=sa.text('now()'), nullable=True))
    # Quem já existe mora na unidade desde o cadastro.
    op.execute("UPDATE usuarios SET unidade_desde = criado_em")
    op.alter_column('usuarios', 'unidade_desde', nullable=False)


def downgrade() -> None:
    op.drop_column('usuarios', 'unidade_desde')
