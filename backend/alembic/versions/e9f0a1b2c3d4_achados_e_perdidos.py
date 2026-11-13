"""Achados e perdidos da portaria.

achados: o que a portaria encontrou, onde e quando; o morador que disse
"é meu"; a entrega, com o nome de quem retirou; ou, passado o prazo de
guarda, a doação ou o descarte pelo síndico, com o destino.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS = postgresql.ENUM('GUARDADO', 'DEVOLVIDO', 'DESCARTADO', name='status_achado',
                         create_type=False)


def upgrade() -> None:
    STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'achados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('registrado_por_id', sa.Integer(), nullable=True),
        sa.Column('descricao', sa.String(length=200), nullable=False),
        sa.Column('local', sa.String(length=120), nullable=False),
        sa.Column('encontrado_em', sa.Date(), nullable=False),
        sa.Column('status', STATUS, nullable=False),
        sa.Column('reclamado_por_id', sa.Integer(), nullable=True),
        sa.Column('reclamado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('devolvido_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('devolvido_por_id', sa.Integer(), nullable=True),
        sa.Column('entregue_a', sa.String(length=120), nullable=True),
        sa.Column('descartado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('descartado_por_id', sa.Integer(), nullable=True),
        sa.Column('destino', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint(
            "status <> 'DESCARTADO' OR (descartado_em IS NOT NULL AND destino IS NOT NULL)",
            name='ck_achado_descartado'),
        sa.CheckConstraint(
            "status <> 'DEVOLVIDO' OR (devolvido_em IS NOT NULL AND entregue_a IS NOT NULL)",
            name='ck_achado_devolvido'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['descartado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['devolvido_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reclamado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['registrado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_achados_condominio_status', 'achados', ['condominio_id', 'status'])
    op.create_index(op.f('ix_achados_condominio_id'), 'achados', ['condominio_id'])
    op.create_index(op.f('ix_achados_reclamado_por_id'), 'achados', ['reclamado_por_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_achados_reclamado_por_id'), table_name='achados')
    op.drop_index(op.f('ix_achados_condominio_id'), table_name='achados')
    op.drop_index('ix_achados_condominio_status', table_name='achados')
    op.drop_table('achados')
    STATUS.drop(op.get_bind(), checkfirst=True)
