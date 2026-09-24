"""foto da ocorrencia como arquivo

Como as fotos de visitantes e encomendas (bba89722a975): a ocorrência
deixa de aceitar um endereço livre (foto_url) e passa a guardar o nome
de um arquivo gravado pela API (foto_arquivo), entregue só a quem pode
ver a ocorrência.

Revision ID: d4f02c8aa319
Revises: bba89722a975
Create Date: 2026-09-24 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4f02c8aa319'
down_revision: Union[str, None] = 'bba89722a975'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Um endereço digitado não é um arquivo gravado pela API.
    op.execute('UPDATE ocorrencias SET foto_url = NULL')
    op.alter_column(
        'ocorrencias', 'foto_url', new_column_name='foto_arquivo',
        type_=sa.String(length=100), existing_type=sa.VARCHAR(length=500),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'ocorrencias', 'foto_arquivo', new_column_name='foto_url',
        type_=sa.VARCHAR(length=500), existing_type=sa.String(length=100),
        existing_nullable=True,
    )
