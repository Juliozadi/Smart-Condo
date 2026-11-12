"""Acordo de parcelamento das cobranças vencidas.

acordos: as cobranças vencidas de um apartamento, com a multa e os juros
do dia (ou dispensados), divididas em parcelas mensais. cobrancas ganha
acordo_id; status_cobranca ganha NEGOCIADA (a cobrança que entrou num
acordo) e origem_cobranca ganha ACORDO (a parcela).

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-11-10 23:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, None] = 'a5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_ANTIGOS = "'ABERTA', 'PAGA', 'VENCIDA', 'CANCELADA'"
ORIGENS_ANTIGAS = "'TAXA', 'MULTA', 'USO_ESPACO'"
INDICE_TAXA = ("CREATE UNIQUE INDEX uq_cobranca_competencia ON cobrancas "
               "(unidade_id, competencia) "
               "WHERE status <> 'CANCELADA' AND origem = 'TAXA'")


def upgrade() -> None:
    op.execute("ALTER TYPE status_cobranca ADD VALUE IF NOT EXISTS 'NEGOCIADA'")
    op.execute("ALTER TYPE origem_cobranca ADD VALUE IF NOT EXISTS 'ACORDO'")
    op.create_table(
        'acordos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('criado_por_id', sa.Integer(), nullable=True),
        sa.Column('principal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('encargos', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('dispensou_encargos', sa.Boolean(), server_default=sa.text('false'),
                  nullable=False),
        sa.Column('parcelas', sa.Integer(), nullable=False),
        sa.Column('primeiro_vencimento', sa.Date(), nullable=False),
        sa.Column('observacao', sa.String(length=300), nullable=True),
        sa.Column('cancelado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelado_por_id', sa.Integer(), nullable=True),
        sa.Column('motivo_cancelamento', sa.String(length=300), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                  nullable=False),
        sa.CheckConstraint('encargos >= 0', name='ck_acordo_encargos'),
        sa.CheckConstraint('parcelas BETWEEN 1 AND 24', name='ck_acordo_parcelas'),
        sa.CheckConstraint('principal > 0', name='ck_acordo_principal'),
        sa.CheckConstraint('total = principal + encargos', name='ck_acordo_total'),
        sa.ForeignKeyConstraint(['cancelado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_acordos_condominio_id'), 'acordos', ['condominio_id'])
    op.create_index(op.f('ix_acordos_unidade_id'), 'acordos', ['unidade_id'])
    op.add_column('cobrancas', sa.Column('acordo_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_cobrancas_acordo_id'), 'cobrancas', ['acordo_id'])
    op.create_foreign_key('cobrancas_acordo_id_fkey', 'cobrancas', 'acordos', ['acordo_id'],
                          ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Sem acordos, as parcelas saem e as cobranças negociadas voltam a
    # ser devidas como eram.
    op.execute("DELETE FROM cobrancas WHERE origem = 'ACORDO'")
    op.execute("UPDATE cobrancas SET status = CASE WHEN vencimento < CURRENT_DATE "
               "THEN 'VENCIDA'::status_cobranca ELSE 'ABERTA'::status_cobranca END "
               "WHERE status = 'NEGOCIADA'")
    op.drop_constraint('cobrancas_acordo_id_fkey', 'cobrancas', type_='foreignkey')
    op.drop_index(op.f('ix_cobrancas_acordo_id'), table_name='cobrancas')
    op.drop_column('cobrancas', 'acordo_id')
    op.drop_index(op.f('ix_acordos_unidade_id'), table_name='acordos')
    op.drop_index(op.f('ix_acordos_condominio_id'), table_name='acordos')
    op.drop_table('acordos')

    # O PostgreSQL não remove valor de enum: recria os tipos sem eles. O
    # índice da taxa do mês compara com os tipos e sai antes, volta depois.
    op.execute("DROP INDEX uq_cobranca_competencia")
    op.execute("ALTER TYPE status_cobranca RENAME TO status_cobranca_antigo")
    op.execute(f"CREATE TYPE status_cobranca AS ENUM ({STATUS_ANTIGOS})")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN status TYPE status_cobranca "
               "USING status::text::status_cobranca")
    op.execute("DROP TYPE status_cobranca_antigo")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem DROP DEFAULT")
    op.execute("ALTER TYPE origem_cobranca RENAME TO origem_cobranca_antigo")
    op.execute(f"CREATE TYPE origem_cobranca AS ENUM ({ORIGENS_ANTIGAS})")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem TYPE origem_cobranca "
               "USING origem::text::origem_cobranca")
    op.execute("ALTER TABLE cobrancas ALTER COLUMN origem SET DEFAULT 'TAXA'")
    op.execute("DROP TYPE origem_cobranca_antigo")
    op.execute(INDICE_TAXA)
