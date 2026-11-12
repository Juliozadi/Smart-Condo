"""Regras de mudança de cada condomínio.

O regimento muda de um condomínio para outro: o aviso mínimo vai para
condominios.mudanca_antecedencia_dias, e os dias e horários permitidos
para horarios_mudanca (o dia sem linha não tem mudança). Sem nenhuma
linha, vale a regra padrão da API.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-10-25 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('condominios', sa.Column('mudanca_antecedencia_dias', sa.Integer(),
                                           server_default=sa.text('2'), nullable=False))
    op.create_check_constraint('ck_condominio_mudanca_antecedencia', 'condominios',
                               'mudanca_antecedencia_dias BETWEEN 0 AND 60')
    op.create_table(
        'horarios_mudanca',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.Integer(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fim', sa.Time(), nullable=False),
        sa.CheckConstraint('dia_semana BETWEEN 1 AND 7', name='ck_horario_mudanca_dia'),
        sa.CheckConstraint('hora_fim > hora_inicio', name='ck_horario_mudanca_intervalo'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('condominio_id', 'dia_semana', name='uq_horario_mudanca_dia'),
    )
    op.create_index(op.f('ix_horarios_mudanca_condominio_id'), 'horarios_mudanca',
                    ['condominio_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_horarios_mudanca_condominio_id'), table_name='horarios_mudanca')
    op.drop_table('horarios_mudanca')
    op.drop_constraint('ck_condominio_mudanca_antecedencia', 'condominios', type_='check')
    op.drop_column('condominios', 'mudanca_antecedencia_dias')
