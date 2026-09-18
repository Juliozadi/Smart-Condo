"""papel de administrador

Revision ID: a36d1fb5ea68
Revises: a684b94fc284
Create Date: 2026-09-18 22:36:25.686397
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a36d1fb5ea68'
down_revision: Union[str, None] = 'a684b94fc284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # O autogenerate não enxerga valores novos num ENUM do PostgreSQL, então
    # a alteração é escrita à mão. O SQLAlchemy grava os NOMES do enum do
    # Python, que são maiúsculos — por isso 'ADMIN' e não 'admin'.
    op.execute("ALTER TYPE papel_usuario ADD VALUE IF NOT EXISTS 'ADMIN'")


def downgrade() -> None:
    # O PostgreSQL não remove um valor de ENUM; o tipo precisa ser recriado.
    # Os administradores saem antes, senão a conversão falha por encontrar
    # um valor que não existe mais no tipo novo.
    op.execute("DELETE FROM usuarios WHERE papel = 'ADMIN'")
    op.execute("ALTER TYPE papel_usuario RENAME TO papel_usuario_antigo")
    op.execute("CREATE TYPE papel_usuario AS ENUM ('SINDICO', 'PORTEIRO', 'MORADOR')")
    op.execute(
        "ALTER TABLE usuarios ALTER COLUMN papel TYPE papel_usuario "
        "USING papel::text::papel_usuario"
    )
    op.execute("DROP TYPE papel_usuario_antigo")
