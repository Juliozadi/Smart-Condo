"""Medição individual de água e gás.

leituras_consumo: a leitura de cada mês no medidor de cada apartamento, o
consumo (diferença para a anterior), a troca de medidor, o alerta de
consumo fora do normal e a cobrança gerada; origem_cobranca ganha CONSUMO;
permissoes_porteiro ganha registrar_leituras (desligada por padrão).

Revision ID: a1b2c3d4e5f7
Revises: f0a1b2c3d4e5
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPO = postgresql.ENUM('AGUA', 'GAS', name='tipo_consumo', create_type=False)
ORIGENS_ANTIGAS = "'TAXA', 'MULTA', 'USO_ESPACO', 'ACORDO', 'EXTRA'"
INDICE_TAXA = ("CREATE UNIQUE INDEX uq_cobranca_competencia ON cobrancas "
               "(unidade_id, competencia) "
               "WHERE status <> 'CANCELADA' AND origem = 'TAXA'")


def upgrade() -> None:
    op.execute("ALTER TYPE origem_cobranca ADD VALUE IF NOT EXISTS 'CONSUMO'")
    op.add_column('permissoes_porteiro', sa.Column(
        'registrar_leituras', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    TIPO.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'leituras_consumo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('tipo', TIPO, nullable=False),
        sa.Column('competencia', sa.Date(), nullable=False),
        sa.Column('leitura', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('consumo', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('troca_medidor', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('acima_do_normal', sa.Boolean(), server_default=sa.text('false'),
                  nullable=False),
        sa.Column('observacao', sa.String(length=200), nullable=True),
        sa.Column('registrada_por_id', sa.Integer(), nullable=True),
        sa.Column('cobranca_id', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint('consumo IS NULL OR consumo >= 0', name='ck_leitura_consumo'),
        sa.CheckConstraint('leitura >= 0', name='ck_leitura_valor'),
        sa.ForeignKeyConstraint(['cobranca_id'], ['cobrancas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['registrada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('unidade_id', 'tipo', 'competencia', name='uq_leitura_competencia'),
    )
    op.create_index('ix_leituras_condominio_competencia', 'leituras_consumo',
                    ['condominio_id', 'tipo', 'competencia'])
    op.create_index(op.f('ix_leituras_consumo_cobranca_id'), 'leituras_consumo', ['cobranca_id'])
    op.create_index(op.f('ix_leituras_consumo_condominio_id'), 'leituras_consumo',
                    ['condominio_id'])
    op.create_index(op.f('ix_leituras_consumo_unidade_id'), 'leituras_consumo', ['unidade_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_leituras_consumo_unidade_id'), table_name='leituras_consumo')
    op.drop_index(op.f('ix_leituras_consumo_condominio_id'), table_name='leituras_consumo')
    op.drop_index(op.f('ix_leituras_consumo_cobranca_id'), table_name='leituras_consumo')
    op.drop_index('ix_leituras_condominio_competencia', table_name='leituras_consumo')
    op.drop_table('leituras_consumo')
    TIPO.drop(op.get_bind(), checkfirst=True)
    op.drop_column('permissoes_porteiro', 'registrar_leituras')
    # Sem medição, as cobranças de consumo saem; o PostgreSQL não remove
    # valor de enum, então o tipo é recriado sem ele.
    op.execute("DELETE FROM cobrancas WHERE origem = 'CONSUMO'")
    op.execute("DROP INDEX uq_cobranca_competencia")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem DROP DEFAULT")
    op.execute("ALTER TYPE origem_cobranca RENAME TO origem_cobranca_antigo")
    op.execute(f"CREATE TYPE origem_cobranca AS ENUM ({ORIGENS_ANTIGAS})")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem TYPE origem_cobranca "
               "USING origem::text::origem_cobranca")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem SET DEFAULT 'TAXA'")
    op.execute("DROP TYPE origem_cobranca_antigo")
    op.execute(INDICE_TAXA)
