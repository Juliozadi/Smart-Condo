"""Manutenção preventiva e obrigações com vencimento.

planos_manutencao (o que vence de tempos em tempos: AVCB, extintores,
caixa d'água, elevadores; a periodicidade e o próximo vencimento) e
realizacoes_manutencao (cada vez que foi feito, com o custo e a despesa
lançada com ele).

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-10-26 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planos_manutencao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.Column('periodicidade_meses', sa.Integer(), nullable=False),
        sa.Column('proximo_vencimento', sa.Date(), nullable=False),
        sa.Column('antecedencia_aviso_dias', sa.Integer(), server_default=sa.text('30'),
                  nullable=False),
        sa.Column('fornecedor', sa.String(length=120), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('ultima_realizacao', sa.Date(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('antecedencia_aviso_dias BETWEEN 0 AND 180',
                           name='ck_plano_manutencao_antecedencia'),
        sa.CheckConstraint('periodicidade_meses BETWEEN 1 AND 120',
                           name='ck_plano_manutencao_periodicidade'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='planos_manutencao_inativado_por_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_planos_manutencao_condominio_id'), 'planos_manutencao',
                    ['condominio_id'])
    op.create_index('uq_plano_manutencao_nome', 'planos_manutencao',
                    ['condominio_id', sa.literal_column('lower(nome)')], unique=True,
                    postgresql_where=sa.text('inativo_em IS NULL'))
    op.create_table(
        'realizacoes_manutencao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plano_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('custo', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('registrada_por_id', sa.Integer(), nullable=True),
        sa.Column('despesa_id', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint('custo IS NULL OR custo > 0', name='ck_realizacao_manutencao_custo'),
        sa.ForeignKeyConstraint(['despesa_id'], ['despesas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plano_id'], ['planos_manutencao.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['registrada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_realizacoes_manutencao_plano_id'), 'realizacoes_manutencao',
                    ['plano_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_realizacoes_manutencao_plano_id'), table_name='realizacoes_manutencao')
    op.drop_table('realizacoes_manutencao')
    op.drop_index('uq_plano_manutencao_nome', table_name='planos_manutencao',
                  postgresql_where=sa.text('inativo_em IS NULL'))
    op.drop_index(op.f('ix_planos_manutencao_condominio_id'), table_name='planos_manutencao')
    op.drop_table('planos_manutencao')
