"""Declaração de quitação condominial.

declaracoes_quitacao: a declaração de que o apartamento não tinha débito
vencido, com o código que qualquer um confere e o que ela dizia no dia
(condomínio, apartamento, síndico). Não se apaga; o síndico revoga com
motivo.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-10-26 21:46:19.198395
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'declaracoes_quitacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('emitida_por_id', sa.Integer(), nullable=True),
        sa.Column('codigo', sa.String(length=16), nullable=False),
        sa.Column('referencia_ate', sa.Date(), nullable=False),
        sa.Column('valida_ate', sa.Date(), nullable=False),
        sa.Column('condominio_nome', sa.String(length=160), nullable=False),
        sa.Column('condominio_cnpj', sa.String(length=18), nullable=False),
        sa.Column('identificacao_unidade', sa.String(length=45), nullable=False),
        sa.Column('sindico_nome', sa.String(length=160), nullable=True),
        sa.Column('emitida_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('revogada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revogada_por_id', sa.Integer(), nullable=True),
        sa.Column('motivo_revogacao', sa.Text(), nullable=True),
        sa.CheckConstraint('(revogada_em IS NULL) = (motivo_revogacao IS NULL)',
                           name='ck_declaracao_revogacao'),
        sa.CheckConstraint('valida_ate >= referencia_ate', name='ck_declaracao_validade'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['emitida_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['revogada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )
    op.create_index(op.f('ix_declaracoes_quitacao_condominio_id'), 'declaracoes_quitacao',
                    ['condominio_id'])
    op.create_index(op.f('ix_declaracoes_quitacao_unidade_id'), 'declaracoes_quitacao',
                    ['unidade_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_declaracoes_quitacao_unidade_id'), table_name='declaracoes_quitacao')
    op.drop_index(op.f('ix_declaracoes_quitacao_condominio_id'),
                  table_name='declaracoes_quitacao')
    op.drop_table('declaracoes_quitacao')
