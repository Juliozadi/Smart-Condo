"""Multa e juros da cobrança paga com atraso.

Cada condomínio define a multa (até 2%) e os juros ao mês (até 1%),
pelo Código Civil, art. 1.336, § 1º; os que já existem ficam com os
valores da lei. pagamentos.encargos guarda quanto de cada pagamento foi
para multa e juros — os pagamentos antigos, nada.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-10-14 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('condominios', sa.Column('multa_atraso', sa.Numeric(4, 2), nullable=False,
                                           server_default=sa.text('2.00')))
    op.add_column('condominios', sa.Column('juros_mensais', sa.Numeric(4, 2), nullable=False,
                                           server_default=sa.text('1.00')))
    op.create_check_constraint('ck_condominio_multa', 'condominios',
                               'multa_atraso BETWEEN 0 AND 2')
    op.create_check_constraint('ck_condominio_juros', 'condominios',
                               'juros_mensais BETWEEN 0 AND 1')
    op.add_column('pagamentos', sa.Column('encargos', sa.Numeric(10, 2), nullable=False,
                                          server_default=sa.text('0')))
    op.create_check_constraint('ck_pagamento_encargos', 'pagamentos',
                               'encargos >= 0 AND encargos <= valor')


def downgrade() -> None:
    op.drop_constraint('ck_pagamento_encargos', 'pagamentos', type_='check')
    op.drop_column('pagamentos', 'encargos')
    op.drop_constraint('ck_condominio_juros', 'condominios', type_='check')
    op.drop_constraint('ck_condominio_multa', 'condominios', type_='check')
    op.drop_column('condominios', 'juros_mensais')
    op.drop_column('condominios', 'multa_atraso')
