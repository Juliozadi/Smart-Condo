"""Uma pessoa, vários perfis.

O síndico que também mora, o morador eleito síndico e o dono de mais de
um apartamento: cada perfil é um cadastro vinculado ao cadastro com
login da pessoa (conta_principal_id). E-mail e CPF continuam únicos
entre os cadastros principais. reside separa o proprietário que não
mora no apartamento.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-10-22 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = 'd6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('reside', sa.Boolean(), server_default=sa.text('true'),
                                        nullable=False))
    op.add_column('usuarios', sa.Column('conta_principal_id', sa.Integer(), nullable=True))
    op.create_foreign_key('usuarios_conta_principal_id_fkey', 'usuarios', 'usuarios',
                          ['conta_principal_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_usuarios_conta_principal_id'), 'usuarios', ['conta_principal_id'])

    op.drop_index('ix_usuarios_email', table_name='usuarios')
    op.drop_index('ix_usuarios_cpf', table_name='usuarios')
    op.create_index('ix_usuarios_email', 'usuarios', ['email'])
    op.create_index('ix_usuarios_cpf', 'usuarios', ['cpf'])
    op.create_index('uq_usuarios_email_principal', 'usuarios', ['email'], unique=True,
                    postgresql_where=sa.text('conta_principal_id IS NULL'))
    op.create_index('uq_usuarios_cpf_principal', 'usuarios', ['cpf'], unique=True,
                    postgresql_where=sa.text('conta_principal_id IS NULL'))


def downgrade() -> None:
    # Sem a coluna, os perfis vinculados repetiriam e-mail e CPF: saem.
    op.execute('DELETE FROM usuarios WHERE conta_principal_id IS NOT NULL')
    op.drop_index('uq_usuarios_cpf_principal', table_name='usuarios')
    op.drop_index('uq_usuarios_email_principal', table_name='usuarios')
    op.drop_index('ix_usuarios_cpf', table_name='usuarios')
    op.drop_index('ix_usuarios_email', table_name='usuarios')
    op.create_index('ix_usuarios_email', 'usuarios', ['email'], unique=True)
    op.create_index('ix_usuarios_cpf', 'usuarios', ['cpf'], unique=True)

    op.drop_index(op.f('ix_usuarios_conta_principal_id'), table_name='usuarios')
    op.drop_constraint('usuarios_conta_principal_id_fkey', 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'conta_principal_id')
    op.drop_column('usuarios', 'reside')
