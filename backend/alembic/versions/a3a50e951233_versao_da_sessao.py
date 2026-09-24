"""Versão da sessão: trocar a senha encerra as sessões abertas.

Cada token carrega a versão com que foi emitido; a troca ou a
redefinição da senha aumenta a do usuário, e os tokens antigos deixam de
valer. Começa em 0, o que mantém válidas as sessões abertas hoje.

Revision ID: a3a50e951233
Revises: 1eb812cceaae
Create Date: 2026-09-24 15:34:54.955379
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3a50e951233'
down_revision: Union[str, None] = '1eb812cceaae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('versao_sessao', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('usuarios', 'versao_sessao')
