"""Assembleia virtual: convocação, pauta e votos por apartamento.

Código Civil, art. 1.354-A (Lei 14.309/2022): a assembleia pode ser
eletrônica. votos tem um voto por apartamento em cada item
(uq_voto_por_unidade).

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-10-20 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assembleias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('convocada_por_id', sa.Integer(), nullable=True),
        sa.Column('titulo', sa.String(length=180), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('abre_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('encerra_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('motivo_cancelamento', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('encerra_em > abre_em', name='ck_assembleia_periodo'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['convocada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL',
                                name='assembleias_inativado_por_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assembleias_condominio_id'), 'assembleias', ['condominio_id'])
    op.create_index(op.f('ix_assembleias_convocada_por_id'), 'assembleias',
                    ['convocada_por_id'])

    op.create_table(
        'itens_pauta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assembleia_id', sa.Integer(), nullable=False),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=180), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('maioria', sa.Enum('SIMPLES', 'DOIS_TERCOS', 'UNANIMIDADE',
                                     name='maioria_exigida'), nullable=False),
        sa.ForeignKeyConstraint(['assembleia_id'], ['assembleias.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_itens_pauta_assembleia_id'), 'itens_pauta', ['assembleia_id'])

    op.create_table(
        'votos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('escolha', sa.Enum('A_FAVOR', 'CONTRA', 'ABSTENCAO', name='escolha_voto'),
                  nullable=False),
        sa.Column('votado_em', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['itens_pauta.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id', 'unidade_id', name='uq_voto_por_unidade'),
    )
    op.create_index(op.f('ix_votos_item_id'), 'votos', ['item_id'])
    op.create_index(op.f('ix_votos_unidade_id'), 'votos', ['unidade_id'])
    op.create_index(op.f('ix_votos_usuario_id'), 'votos', ['usuario_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_votos_usuario_id'), table_name='votos')
    op.drop_index(op.f('ix_votos_unidade_id'), table_name='votos')
    op.drop_index(op.f('ix_votos_item_id'), table_name='votos')
    op.drop_table('votos')
    op.drop_index(op.f('ix_itens_pauta_assembleia_id'), table_name='itens_pauta')
    op.drop_table('itens_pauta')
    op.drop_index(op.f('ix_assembleias_convocada_por_id'), table_name='assembleias')
    op.drop_index(op.f('ix_assembleias_condominio_id'), table_name='assembleias')
    op.drop_table('assembleias')
    sa.Enum(name='escolha_voto').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='maioria_exigida').drop(op.get_bind(), checkfirst=False)
