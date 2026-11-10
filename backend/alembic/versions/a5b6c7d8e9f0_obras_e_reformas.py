"""Obras e reformas nos apartamentos.

reformas: o que o morador vai fazer, o prazo, a empresa e — quando mexe em
estrutura, vedações ou instalações — o responsável técnico e a ART ou RRT
(NBR 16280); a avaliação do síndico, com as condições ou o motivo da
recusa; o cancelamento e a conclusão.

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-11-10 22:13:30.938527
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a5b6c7d8e9f0'
down_revision: Union[str, None] = 'f4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS = postgresql.ENUM('PENDENTE', 'APROVADA', 'RECUSADA', 'CANCELADA', 'CONCLUIDA',
                         name='status_reforma', create_type=False)


def upgrade() -> None:
    STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'reformas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('solicitada_por_id', sa.Integer(), nullable=True),
        sa.Column('descricao', sa.String(length=500), nullable=False),
        sa.Column('empresa', sa.String(length=120), nullable=True),
        sa.Column('altera_estrutura', sa.Boolean(), server_default=sa.text('false'),
                  nullable=False),
        sa.Column('responsavel_tecnico', sa.String(length=160), nullable=True),
        sa.Column('art_rrt', sa.String(length=40), nullable=True),
        sa.Column('inicio', sa.Date(), nullable=False),
        sa.Column('fim', sa.Date(), nullable=False),
        sa.Column('status', STATUS, nullable=False),
        sa.Column('avaliada_por_id', sa.Integer(), nullable=True),
        sa.Column('avaliada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('condicoes', sa.String(length=300), nullable=True),
        sa.Column('motivo_recusa', sa.String(length=300), nullable=True),
        sa.Column('cancelada_por_id', sa.Integer(), nullable=True),
        sa.Column('cancelada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_cancelamento', sa.String(length=300), nullable=True),
        sa.Column('concluida_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint(
            'NOT altera_estrutura OR (responsavel_tecnico IS NOT NULL AND art_rrt IS NOT NULL)',
            name='ck_reforma_responsavel'),
        sa.CheckConstraint('fim >= inicio', name='ck_reforma_prazo'),
        sa.ForeignKeyConstraint(['avaliada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cancelada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['solicitada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reformas_condominio_fim', 'reformas', ['condominio_id', 'fim'])
    op.create_index(op.f('ix_reformas_condominio_id'), 'reformas', ['condominio_id'])
    op.create_index(op.f('ix_reformas_solicitada_por_id'), 'reformas', ['solicitada_por_id'])
    op.create_index(op.f('ix_reformas_status'), 'reformas', ['status'])
    op.create_index(op.f('ix_reformas_unidade_id'), 'reformas', ['unidade_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_reformas_unidade_id'), table_name='reformas')
    op.drop_index(op.f('ix_reformas_status'), table_name='reformas')
    op.drop_index(op.f('ix_reformas_solicitada_por_id'), table_name='reformas')
    op.drop_index(op.f('ix_reformas_condominio_id'), table_name='reformas')
    op.drop_index('ix_reformas_condominio_fim', table_name='reformas')
    op.drop_table('reformas')
    STATUS.drop(op.get_bind(), checkfirst=True)
