"""Agendamento de mudança.

O morador pede o dia e o horário, o síndico aprova ou recusa, e a
portaria vê as aprovadas.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-10-21 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPO = postgresql.ENUM('CHEGADA', 'SAIDA', name='tipo_mudanca', create_type=False)
STATUS = postgresql.ENUM('PENDENTE', 'APROVADA', 'RECUSADA', 'CANCELADA', 'CONCLUIDA',
                         name='status_mudanca', create_type=False)


def upgrade() -> None:
    TIPO.create(op.get_bind(), checkfirst=True)
    STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'mudancas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('solicitada_por_id', sa.Integer(), nullable=True),
        sa.Column('tipo', TIPO, nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fim', sa.Time(), nullable=False),
        sa.Column('empresa', sa.String(length=120), nullable=True),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.Column('status', STATUS, nullable=False),
        sa.Column('avaliada_por_id', sa.Integer(), nullable=True),
        sa.Column('avaliada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_recusa', sa.String(length=300), nullable=True),
        sa.Column('cancelada_por_id', sa.Integer(), nullable=True),
        sa.Column('cancelada_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_cancelamento', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint('hora_fim > hora_inicio', name='ck_mudanca_intervalo'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['solicitada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['avaliada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cancelada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_mudancas_condominio_id'), 'mudancas', ['condominio_id'])
    op.create_index(op.f('ix_mudancas_unidade_id'), 'mudancas', ['unidade_id'])
    op.create_index(op.f('ix_mudancas_solicitada_por_id'), 'mudancas', ['solicitada_por_id'])
    op.create_index(op.f('ix_mudancas_status'), 'mudancas', ['status'])
    op.create_index('ix_mudancas_condominio_data', 'mudancas', ['condominio_id', 'data'])


def downgrade() -> None:
    op.drop_index('ix_mudancas_condominio_data', table_name='mudancas')
    op.drop_index(op.f('ix_mudancas_status'), table_name='mudancas')
    op.drop_index(op.f('ix_mudancas_solicitada_por_id'), table_name='mudancas')
    op.drop_index(op.f('ix_mudancas_unidade_id'), table_name='mudancas')
    op.drop_index(op.f('ix_mudancas_condominio_id'), table_name='mudancas')
    op.drop_table('mudancas')
    STATUS.drop(op.get_bind(), checkfirst=True)
    TIPO.drop(op.get_bind(), checkfirst=True)
