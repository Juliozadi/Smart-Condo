"""documentos do condominio como arquivo

Os documentos do condomínio guardavam um endereço digitado (arquivo_url),
que nos dados de demonstração nem existia e podia ser um "javascript:"
executado no clique do morador. Passam a guardar o arquivo enviado pela
API (arquivo), com o tipo conferido pelo conteúdo (tipo_conteudo).

Os endereços antigos não viram arquivo: o documento fica sem arquivo
disponível, e o síndico pode publicá-lo de novo.

Revision ID: 1eb812cceaae
Revises: d4f02c8aa319
Create Date: 2026-09-24 14:44:11.095298
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1eb812cceaae'
down_revision: Union[str, None] = 'd4f02c8aa319'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Em três passos: o PostgreSQL troca o tipo antes de liberar o vazio,
    # e o USING NULL esbarraria no NOT NULL.
    op.alter_column('documentos', 'arquivo_url', nullable=True,
                    existing_type=sa.VARCHAR(length=500))
    op.alter_column('documentos', 'arquivo_url', type_=sa.String(length=100),
                    existing_type=sa.VARCHAR(length=500), postgresql_using='NULL')
    op.alter_column('documentos', 'arquivo_url', new_column_name='arquivo')
    op.add_column('documentos', sa.Column('tipo_conteudo', sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column('documentos', 'tipo_conteudo')
    # Sem o endereço de antes, o que sobra é um marcador: a coluna antiga
    # não aceitava vazio.
    op.execute("UPDATE documentos SET arquivo = 'indisponivel' WHERE arquivo IS NULL")
    op.alter_column(
        'documentos', 'arquivo', new_column_name='arquivo_url',
        type_=sa.VARCHAR(length=500), existing_type=sa.String(length=100),
        nullable=False, existing_nullable=True,
    )
