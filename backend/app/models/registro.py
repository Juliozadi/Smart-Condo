"""Registro de alterações: quem fez o quê, em qual registro e quando.

Pedido do grupo: com mais de um administrador, cada criação, edição ou
inativação precisa mostrar quem a fez ("editado por fulano"). Uma tabela
só, para todas as entidades, guarda a história inteira — a linha do
registro mostra a última alteração, e a janela de edição, todas.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class RegistroAlteracao(Base):
    __tablename__ = "registros_alteracao"
    __table_args__ = (Index("ix_registros_alteracao_entidade", "entidade", "entidade_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nulo só se o autor deixar de existir; usuários não são apagados.
    autor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    acao: Mapped[str] = mapped_column(String(20), nullable=False)
    entidade: Mapped[str] = mapped_column(String(30), nullable=False)
    entidade_id: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    feito_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    autor: Mapped["Usuario | None"] = relationship(foreign_keys=[autor_id])

    def __repr__(self) -> str:
        return f"<RegistroAlteracao {self.entidade}#{self.entidade_id} {self.acao}>"
