"""Veículos cadastrados do apartamento.

A portaria só registrava as passagens, sem saber quais placas são dos
moradores. A placa fica ativa em um apartamento por vez
(uq_veiculo_placa_ativa); remover é inativar.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-10-21 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'veiculos_unidade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('cadastrado_por_id', sa.Integer(), nullable=True),
        sa.Column('placa', sa.String(length=10), nullable=False),
        sa.Column('modelo', sa.String(length=60), nullable=True),
        sa.Column('cor', sa.String(length=30), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cadastrado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='veiculos_unidade_inativado_por_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_veiculos_unidade_condominio_id'), 'veiculos_unidade',
                    ['condominio_id'])
    op.create_index(op.f('ix_veiculos_unidade_unidade_id'), 'veiculos_unidade', ['unidade_id'])
    op.create_index(op.f('ix_veiculos_unidade_cadastrado_por_id'), 'veiculos_unidade',
                    ['cadastrado_por_id'])
    op.create_index('uq_veiculo_placa_ativa', 'veiculos_unidade', ['condominio_id', 'placa'],
                    unique=True, postgresql_where=sa.text('inativo_em IS NULL'))


def downgrade() -> None:
    op.drop_index('uq_veiculo_placa_ativa', table_name='veiculos_unidade')
    op.drop_index(op.f('ix_veiculos_unidade_cadastrado_por_id'), table_name='veiculos_unidade')
    op.drop_index(op.f('ix_veiculos_unidade_unidade_id'), table_name='veiculos_unidade')
    op.drop_index(op.f('ix_veiculos_unidade_condominio_id'), table_name='veiculos_unidade')
    op.drop_table('veiculos_unidade')
