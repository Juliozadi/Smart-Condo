"""Animais de estimação dos apartamentos.

animais: o nome, a espécie, o porte, a raça e a cor; a validade da vacina
antirrábica e o último lembrete do síndico; quem cadastrou e a inativação
(nada é apagado).

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, None] = 'e9f0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ESPECIE = postgresql.ENUM('CAO', 'GATO', 'AVE', 'OUTRO', name='especie_animal',
                          create_type=False)
PORTE = postgresql.ENUM('PEQUENO', 'MEDIO', 'GRANDE', name='porte_animal', create_type=False)


def upgrade() -> None:
    ESPECIE.create(op.get_bind(), checkfirst=True)
    PORTE.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'animais',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('cadastrado_por_id', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(length=60), nullable=False),
        sa.Column('especie', ESPECIE, nullable=False),
        sa.Column('raca', sa.String(length=60), nullable=True),
        sa.Column('porte', PORTE, nullable=False),
        sa.Column('cor', sa.String(length=40), nullable=True),
        sa.Column('vacina_antirrabica_ate', sa.Date(), nullable=True),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.Column('lembrete_vacina_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('inativo_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inativado_por_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cadastrado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inativado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_animais_cadastrado_por_id'), 'animais', ['cadastrado_por_id'])
    op.create_index(op.f('ix_animais_condominio_id'), 'animais', ['condominio_id'])
    op.create_index(op.f('ix_animais_unidade_id'), 'animais', ['unidade_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_animais_unidade_id'), table_name='animais')
    op.drop_index(op.f('ix_animais_condominio_id'), table_name='animais')
    op.drop_index(op.f('ix_animais_cadastrado_por_id'), table_name='animais')
    op.drop_table('animais')
    PORTE.drop(op.get_bind(), checkfirst=True)
    ESPECIE.drop(op.get_bind(), checkfirst=True)
