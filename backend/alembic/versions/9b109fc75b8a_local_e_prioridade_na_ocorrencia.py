"""local e prioridade na ocorrencia

Revision ID: 9b109fc75b8a
Revises: 890a8059b8a1
Create Date: 2026-09-21 07:29:16.536983
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9b109fc75b8a'
down_revision: Union[str, None] = '890a8059b8a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


prioridade = sa.Enum(
    'BAIXA', 'NORMAL', 'ALTA', 'URGENTE', name='prioridade_ocorrencia'
)


def upgrade() -> None:
    prioridade.create(op.get_bind(), checkfirst=True)

    op.add_column('ocorrencias', sa.Column('local', sa.String(length=120), nullable=True))
    # As ocorrências que já existem entram como prioridade normal; o
    # server_default sai logo em seguida para que a aplicação continue
    # sendo quem define o valor.
    op.add_column(
        'ocorrencias',
        sa.Column('prioridade', prioridade, nullable=False, server_default='NORMAL'),
    )
    op.alter_column('ocorrencias', 'prioridade', server_default=None)
    op.create_index(op.f('ix_ocorrencias_prioridade'), 'ocorrencias', ['prioridade'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ocorrencias_prioridade'), table_name='ocorrencias')
    op.drop_column('ocorrencias', 'prioridade')
    op.drop_column('ocorrencias', 'local')
    # Remover a coluna não apaga o tipo no Postgres; sem isto um upgrade
    # depois do downgrade falharia com "type already exists".
    op.execute('DROP TYPE IF EXISTS prioridade_ocorrencia')
