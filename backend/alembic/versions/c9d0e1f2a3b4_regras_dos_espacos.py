"""Regras de uso de cada espaço.

O síndico define o horário de funcionamento, a antecedência mínima, a
duração máxima e quantas reservas futuras cada apartamento pode ter de
um espaço. Vazio = sem a regra; os espaços que já existem ficam sem.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-10-13 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('espacos_comuns', sa.Column('horario_abertura', sa.Time(), nullable=True))
    op.add_column('espacos_comuns', sa.Column('horario_fechamento', sa.Time(), nullable=True))
    op.add_column('espacos_comuns', sa.Column('antecedencia_minima_dias', sa.Integer(),
                                              nullable=True))
    op.add_column('espacos_comuns', sa.Column('duracao_maxima_horas', sa.Integer(),
                                              nullable=True))
    op.add_column('espacos_comuns', sa.Column('limite_por_unidade', sa.Integer(), nullable=True))
    op.create_check_constraint('ck_espaco_horario', 'espacos_comuns',
                               'horario_fechamento > horario_abertura')


def downgrade() -> None:
    op.drop_constraint('ck_espaco_horario', 'espacos_comuns', type_='check')
    op.drop_column('espacos_comuns', 'limite_por_unidade')
    op.drop_column('espacos_comuns', 'duracao_maxima_horas')
    op.drop_column('espacos_comuns', 'antecedencia_minima_dias')
    op.drop_column('espacos_comuns', 'horario_fechamento')
    op.drop_column('espacos_comuns', 'horario_abertura')
