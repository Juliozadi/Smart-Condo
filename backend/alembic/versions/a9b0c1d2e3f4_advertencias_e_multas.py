"""Advertências e multas por infração do regimento.

Nova tabela infracoes. A cobrança ganha a origem (taxa, multa, uso de
espaço): a taxa condominial continua uma por apartamento e mês, e a
multa entra ao lado dela.

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-10-25 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a9b0c1d2e3f4'
down_revision: Union[str, None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORIGEM = postgresql.ENUM('TAXA', 'MULTA', 'USO_ESPACO', name='origem_cobranca', create_type=False)
TIPO = postgresql.ENUM('ADVERTENCIA', 'MULTA', name='tipo_infracao', create_type=False)
STATUS = postgresql.ENUM('NOTIFICADA', 'DEFESA_APRESENTADA', 'CONFIRMADA', 'ANULADA',
                         name='status_infracao', create_type=False)


def upgrade() -> None:
    for tipo in (ORIGEM, TIPO, STATUS):
        tipo.create(op.get_bind(), checkfirst=True)

    op.add_column('cobrancas', sa.Column('origem', ORIGEM, server_default=sa.text("'TAXA'"),
                                         nullable=False))
    op.drop_index('uq_cobranca_competencia', table_name='cobrancas')
    op.create_index('uq_cobranca_competencia', 'cobrancas', ['unidade_id', 'competencia'],
                    unique=True,
                    postgresql_where=sa.text("status <> 'CANCELADA' AND origem = 'TAXA'"))

    op.create_table(
        'infracoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('aplicada_por_id', sa.Integer(), nullable=True),
        sa.Column('tipo', TIPO, nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('artigo', sa.String(length=120), nullable=True),
        sa.Column('ocorrida_em', sa.Date(), nullable=False),
        sa.Column('valor', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('prazo_defesa', sa.Date(), nullable=False),
        sa.Column('status', STATUS, nullable=False),
        sa.Column('defesa', sa.Text(), nullable=True),
        sa.Column('defesa_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('defesa_por_id', sa.Integer(), nullable=True),
        sa.Column('decisao_motivo', sa.Text(), nullable=True),
        sa.Column('decidida_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decidida_por_id', sa.Integer(), nullable=True),
        sa.Column('cobranca_id', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint("(tipo = 'MULTA' AND valor > 0) OR (tipo = 'ADVERTENCIA' AND valor IS NULL)",
                           name='ck_infracao_valor'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aplicada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['defesa_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['decidida_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cobranca_id'], ['cobrancas.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_infracoes_condominio_id'), 'infracoes', ['condominio_id'])
    op.create_index(op.f('ix_infracoes_status'), 'infracoes', ['status'])
    op.create_index('ix_infracoes_unidade_criado', 'infracoes', ['unidade_id', 'criado_em'])


def downgrade() -> None:
    op.drop_index('ix_infracoes_unidade_criado', table_name='infracoes')
    op.drop_index(op.f('ix_infracoes_status'), table_name='infracoes')
    op.drop_index(op.f('ix_infracoes_condominio_id'), table_name='infracoes')
    op.drop_table('infracoes')
    # Sem a origem, só cabe uma cobrança por mês: as que não são taxa saem.
    op.execute("DELETE FROM cobrancas WHERE origem <> 'TAXA'")
    op.drop_index('uq_cobranca_competencia', table_name='cobrancas')
    op.create_index('uq_cobranca_competencia', 'cobrancas', ['unidade_id', 'competencia'],
                    unique=True, postgresql_where=sa.text("status <> 'CANCELADA'"))
    op.drop_column('cobrancas', 'origem')
    for tipo in (STATUS, TIPO, ORIGEM):
        tipo.drop(op.get_bind(), checkfirst=True)
