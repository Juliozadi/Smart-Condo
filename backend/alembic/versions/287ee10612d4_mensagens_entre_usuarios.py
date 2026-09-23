"""mensagens entre usuarios

O chat entre síndico, porteiros e moradores (seção 13.5.2).

Revision ID: 287ee10612d4
Revises: a2654fa3a1af
Create Date: 2026-09-23 03:26:46.924787
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '287ee10612d4'
down_revision: Union[str, None] = 'a2654fa3a1af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('mensagens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('condominio_id', sa.Integer(), nullable=False),
    sa.Column('remetente_id', sa.Integer(), nullable=False),
    sa.Column('destinatario_id', sa.Integer(), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('enviada_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('lida_em', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('char_length(texto) BETWEEN 1 AND 2000', name='ck_mensagem_tamanho'),
    sa.CheckConstraint('remetente_id <> destinatario_id', name='ck_mensagem_para_outra_pessoa'),
    sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['destinatario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['remetente_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mensagens_condominio_id'), 'mensagens', ['condominio_id'], unique=False)
    op.create_index('ix_mensagens_conversa', 'mensagens', ['remetente_id', 'destinatario_id', 'id'], unique=False)
    op.create_index('ix_mensagens_nao_lidas', 'mensagens', ['destinatario_id', 'lida_em'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_mensagens_nao_lidas', table_name='mensagens')
    op.drop_index('ix_mensagens_conversa', table_name='mensagens')
    op.drop_index(op.f('ix_mensagens_condominio_id'), table_name='mensagens')
    op.drop_table('mensagens')
