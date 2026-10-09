"""Registro de alterações e inativação no lugar da exclusão.

- registros_alteracao: quem criou, editou, inativou ou reativou cada
  registro, e quando ("editado por fulano").
- condominios, comunicados e documentos ganham inativo_em e
  inativado_por_id: "excluir" passa a inativar, e nada é apagado.

Revision ID: 6689b8d7c72f
Revises: a3a50e951233
Create Date: 2026-09-25 19:22:13.114970
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6689b8d7c72f'
down_revision: Union[str, None] = 'a3a50e951233'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELAS_INATIVAVEIS = ('comunicados', 'condominios', 'documentos')


def upgrade() -> None:
    op.create_table(
        'registros_alteracao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('autor_id', sa.Integer(), nullable=True),
        sa.Column('acao', sa.String(length=20), nullable=False),
        sa.Column('entidade', sa.String(length=30), nullable=False),
        sa.Column('entidade_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('feito_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['autor_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='registros_alteracao_autor_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_registros_alteracao_autor_id', 'registros_alteracao', ['autor_id'])
    op.create_index('ix_registros_alteracao_entidade', 'registros_alteracao',
                    ['entidade', 'entidade_id'])
    for tabela in TABELAS_INATIVAVEIS:
        op.add_column(tabela, sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True))
        op.add_column(tabela, sa.Column('inativado_por_id', sa.Integer(), nullable=True))
        op.create_foreign_key(f'{tabela}_inativado_por_id_fkey', tabela, 'usuarios',
                              ['inativado_por_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    for tabela in TABELAS_INATIVAVEIS:
        op.drop_constraint(f'{tabela}_inativado_por_id_fkey', tabela, type_='foreignkey')
        op.drop_column(tabela, 'inativado_por_id')
        op.drop_column(tabela, 'inativo_em')
    op.drop_index('ix_registros_alteracao_entidade', table_name='registros_alteracao')
    op.drop_index('ix_registros_alteracao_autor_id', table_name='registros_alteracao')
    op.drop_table('registros_alteracao')
