"""registro de quem avaliou o cadastro do usuario

Toda decisão do sistema já registrava autoria — reservas têm
avaliada_por_id/avaliada_em/motivo_recusa, ocorrências têm
respondida_por_id/respondida_em — menos a aprovação de cadastro, que é
a decisão que dá acesso ao sistema.

Revision ID: 04e3d131151e
Revises: 9b109fc75b8a
Create Date: 2026-09-21 19:17:53.634637
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '04e3d131151e'
down_revision: Union[str, None] = '9b109fc75b8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# A chave estrangeira é nomeada de propósito: sem nome, o autogenerate
# gera um drop_constraint(None, ...) que falha na volta.
FK_AVALIADOR = "fk_usuarios_avaliado_por_id_usuarios"


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('avaliado_por_id', sa.Integer(), nullable=True))
    op.add_column('usuarios', sa.Column('avaliado_em', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuarios', sa.Column('motivo_recusa', sa.Text(), nullable=True))
    op.create_foreign_key(
        FK_AVALIADOR, 'usuarios', 'usuarios',
        ['avaliado_por_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(FK_AVALIADOR, 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'motivo_recusa')
    op.drop_column('usuarios', 'avaliado_em')
    op.drop_column('usuarios', 'avaliado_por_id')
