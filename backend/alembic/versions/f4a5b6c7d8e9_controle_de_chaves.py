"""Controle de chaves na portaria.

chaves (o quadro de chaves: as das áreas comuns e as dos apartamentos que
os moradores deixam) e movimentacoes_chave (quem levou, quando, quem
entregou e quem recebeu de volta; uma chave só está fora uma vez).
autorizacoes_visita ganha pode_retirar_chave: quem o morador autoriza a
levar a chave do apartamento.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-10-26 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chaves',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(length=80), nullable=False),
        sa.Column('posicao', sa.String(length=20), nullable=True),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='chaves_inativado_por_id_fkey'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chaves_condominio_id'), 'chaves', ['condominio_id'])
    op.create_index(op.f('ix_chaves_unidade_id'), 'chaves', ['unidade_id'])
    op.create_index('uq_chave_nome', 'chaves',
                    ['condominio_id', sa.literal_column('lower(nome)')], unique=True,
                    postgresql_where=sa.text('inativo_em IS NULL'))
    op.create_table(
        'movimentacoes_chave',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chave_id', sa.Integer(), nullable=False),
        sa.Column('retirada_por_nome', sa.String(length=160), nullable=False),
        sa.Column('retirada_por_documento', sa.String(length=20), nullable=True),
        sa.Column('morador_id', sa.Integer(), nullable=True),
        sa.Column('autorizacao_id', sa.Integer(), nullable=True),
        sa.Column('retirada_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('retirada_registrada_por_id', sa.Integer(), nullable=True),
        sa.Column('devolvida_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('devolucao_registrada_por_id', sa.Integer(), nullable=True),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(['autorizacao_id'], ['autorizacoes_visita.id'],
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['chave_id'], ['chaves.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['devolucao_registrada_por_id'], ['usuarios.id'],
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['morador_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['retirada_registrada_por_id'], ['usuarios.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_movimentacoes_chave_chave_id'), 'movimentacoes_chave', ['chave_id'])
    op.create_index('uq_chave_fora', 'movimentacoes_chave', ['chave_id'], unique=True,
                    postgresql_where=sa.text('devolvida_em IS NULL'))
    op.add_column('autorizacoes_visita',
                  sa.Column('pode_retirar_chave', sa.Boolean(), server_default=sa.text('false'),
                            nullable=False))


def downgrade() -> None:
    op.drop_column('autorizacoes_visita', 'pode_retirar_chave')
    op.drop_index('uq_chave_fora', table_name='movimentacoes_chave',
                  postgresql_where=sa.text('devolvida_em IS NULL'))
    op.drop_index(op.f('ix_movimentacoes_chave_chave_id'), table_name='movimentacoes_chave')
    op.drop_table('movimentacoes_chave')
    op.drop_index('uq_chave_nome', table_name='chaves',
                  postgresql_where=sa.text('inativo_em IS NULL'))
    op.drop_index(op.f('ix_chaves_unidade_id'), table_name='chaves')
    op.drop_index(op.f('ix_chaves_condominio_id'), table_name='chaves')
    op.drop_table('chaves')
