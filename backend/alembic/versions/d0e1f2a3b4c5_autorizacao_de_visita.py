"""Visitante autorizado com antecedência pelo morador.

A diarista de toda terça, o pedreiro da reforma, os convidados da festa:
a portaria registra a entrada sem esperar a resposta do morador.
visitantes.autorizacao_id diz por qual autorização a pessoa entrou.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-10-13 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'autorizacoes_visita',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('autorizado_por_id', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(length=160), nullable=False),
        sa.Column('documento', sa.String(length=20), nullable=True),
        sa.Column('tipo', sa.String(length=60), nullable=False),
        sa.Column('valida_de', sa.Date(), nullable=False),
        sa.Column('valida_ate', sa.Date(), nullable=False),
        sa.Column('dias_semana', sa.String(length=7), nullable=True),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('valida_ate >= valida_de', name='ck_autorizacao_periodo'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['autorizado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='autorizacoes_visita_inativado_por_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_autorizacoes_visita_unidade_id'), 'autorizacoes_visita',
                    ['unidade_id'])
    op.create_index(op.f('ix_autorizacoes_visita_autorizado_por_id'), 'autorizacoes_visita',
                    ['autorizado_por_id'])

    op.add_column('visitantes', sa.Column('autorizacao_id', sa.Integer(), nullable=True))
    op.create_foreign_key('visitantes_autorizacao_id_fkey', 'visitantes', 'autorizacoes_visita',
                          ['autorizacao_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_visitantes_autorizacao_id'), 'visitantes', ['autorizacao_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_visitantes_autorizacao_id'), table_name='visitantes')
    op.drop_constraint('visitantes_autorizacao_id_fkey', 'visitantes', type_='foreignkey')
    op.drop_column('visitantes', 'autorizacao_id')
    op.drop_index(op.f('ix_autorizacoes_visita_autorizado_por_id'),
                  table_name='autorizacoes_visita')
    op.drop_index(op.f('ix_autorizacoes_visita_unidade_id'), table_name='autorizacoes_visita')
    op.drop_table('autorizacoes_visita')
