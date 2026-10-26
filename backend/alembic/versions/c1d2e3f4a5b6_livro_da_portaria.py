"""Livro da portaria: a passagem de turno.

anotacoes_portaria (o que o próximo turno precisa saber; não se apaga nem
se edita) e ciencias_anotacao (quem leu, uma vez por pessoa).

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-10-25 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b0c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'anotacoes_portaria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('autor_id', sa.Integer(), nullable=True),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('importante', sa.Boolean(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['autor_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_anotacoes_portaria_condominio_criado', 'anotacoes_portaria',
                    ['condominio_id', 'criado_em'])
    op.create_table(
        'ciencias_anotacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anotacao_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('ciente_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['anotacao_id'], ['anotacoes_portaria.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('anotacao_id', 'usuario_id', name='uq_ciencia_anotacao'),
    )
    op.create_index(op.f('ix_ciencias_anotacao_anotacao_id'), 'ciencias_anotacao',
                    ['anotacao_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_ciencias_anotacao_anotacao_id'), table_name='ciencias_anotacao')
    op.drop_table('ciencias_anotacao')
    op.drop_index('ix_anotacoes_portaria_condominio_criado', table_name='anotacoes_portaria')
    op.drop_table('anotacoes_portaria')
