"""Peças reaproveitadas pelos modelos."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InativacaoMixin:
    """Nada é apagado: quem "exclui" um registro o inativa. Ele some das
    telas, mas continua no banco, com a data e o autor da inativação."""

    inativo_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @declared_attr
    def inativado_por_id(cls) -> Mapped[int | None]:
        # use_alter: condominios e usuarios já se apontam (síndico e
        # condomínio); criada à parte, a chave não trava a ordem das tabelas.
        return mapped_column(ForeignKey(
            "usuarios.id", ondelete="SET NULL", use_alter=True,
            name=f"{cls.__tablename__}_inativado_por_id_fkey",
        ))

    @property
    def inativo(self) -> bool:
        return self.inativo_em is not None
