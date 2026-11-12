"""Despesas do condomínio: a outra metade da prestação de contas.

O sistema só registrava o que entrava (pagamentos); o síndico passa a
lançar o que sai, e os moradores veem o balancete do mês (Código Civil,
art. 1.348, VIII).

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-10-20 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIAS = ('AGUA', 'ENERGIA', 'LIMPEZA', 'MANUTENCAO', 'SEGURANCA', 'PESSOAL',
              'ADMINISTRACAO', 'OBRAS', 'OUTROS')


def upgrade() -> None:
    op.create_table(
        'despesas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('lancada_por_id', sa.Integer(), nullable=True),
        sa.Column('categoria', sa.Enum(*CATEGORIAS, name='categoria_despesa'), nullable=False),
        sa.Column('descricao', sa.String(length=180), nullable=False),
        sa.Column('valor', sa.Numeric(10, 2), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('fornecedor', sa.String(length=120), nullable=True),
        sa.Column('comprovante_arquivo', sa.String(length=100), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('valor > 0', name='ck_despesa_valor_positivo'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lancada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='despesas_inativado_por_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_despesas_condominio_data', 'despesas', ['condominio_id', 'data'])
    op.create_index(op.f('ix_despesas_lancada_por_id'), 'despesas', ['lancada_por_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_despesas_lancada_por_id'), table_name='despesas')
    op.drop_index('ix_despesas_condominio_data', table_name='despesas')
    op.drop_table('despesas')
    sa.Enum(name='categoria_despesa').drop(op.get_bind(), checkfirst=False)
