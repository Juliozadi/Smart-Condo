"""fotos da portaria e documentos do cadastro

As fotos de visitantes e encomendas deixam de ser um endereço livre
(foto_url) e passam a ser um arquivo gravado pela API (foto_arquivo),
servido só a quem tem direito. E os documentos que o morador envia no
cadastro ganham tabela própria.

Revision ID: bba89722a975
Revises: 287ee10612d4
Create Date: 2026-09-23 14:37:28.112043
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bba89722a975'
down_revision: Union[str, None] = '287ee10612d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('documentos_cadastro',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('IDENTIDADE', 'COMPROVANTE_RESIDENCIA', 'ESCRITURA', name='tipo_documento_cadastro'), nullable=False),
    sa.Column('arquivo', sa.String(length=100), nullable=False),
    sa.Column('tipo_conteudo', sa.String(length=40), nullable=False),
    sa.Column('tamanho_bytes', sa.Integer(), nullable=False),
    sa.Column('enviado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id', 'tipo', name='uq_documento_cadastro_tipo')
    )
    op.create_index(op.f('ix_documentos_cadastro_usuario_id'), 'documentos_cadastro', ['usuario_id'], unique=False)

    for tabela in ('visitantes', 'encomendas'):
        # O que havia ali era um endereço digitado, não um arquivo gravado
        # pela API: não há o que aproveitar, e mantê-lo faria a tela do
        # morador carregar imagem de um servidor de terceiros.
        op.execute(f'UPDATE {tabela} SET foto_url = NULL')
        op.alter_column(
            tabela, 'foto_url', new_column_name='foto_arquivo',
            type_=sa.String(length=100), existing_type=sa.VARCHAR(length=500),
            existing_nullable=True,
        )


def downgrade() -> None:
    for tabela in ('visitantes', 'encomendas'):
        op.alter_column(
            tabela, 'foto_arquivo', new_column_name='foto_url',
            type_=sa.VARCHAR(length=500), existing_type=sa.String(length=100),
            existing_nullable=True,
        )
    op.drop_index(op.f('ix_documentos_cadastro_usuario_id'), table_name='documentos_cadastro')
    op.drop_table('documentos_cadastro')
    # O drop_table do PostgreSQL não remove o tipo ENUM criado junto.
    op.execute('DROP TYPE IF EXISTS tipo_documento_cadastro')
