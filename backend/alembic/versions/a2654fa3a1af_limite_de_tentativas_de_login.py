"""limite de tentativas de login

Sem limite, adivinhar a senha é só questão de tempo. O contador fica no
banco, e não em memória, para sobreviver ao reinício e valer para todos
os processos.

Revision ID: a2654fa3a1af
Revises: 04e3d131151e
Create Date: 2026-09-21 19:35:30.339617
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2654fa3a1af'
down_revision: Union[str, None] = '04e3d131151e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default para as linhas que já existem — sem ele, o NOT NULL
    # quebra numa tabela com usuários cadastrados. Depois o default sai:
    # quem passa a preencher é o modelo.
    op.add_column(
        'usuarios',
        sa.Column('tentativas_login', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('usuarios', 'tentativas_login', server_default=None)
    op.add_column(
        'usuarios',
        sa.Column('bloqueado_ate', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('usuarios', 'bloqueado_ate')
    op.drop_column('usuarios', 'tentativas_login')
