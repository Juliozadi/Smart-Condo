"""Comunicados do síndico.

Documentação, seção 11.5.4: "o Síndico pode fazer comunicados sobre
qualquer assunto que lhe vê importância de repassar aos moradores".
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import CategoriaComunicado

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Comunicado(Base, TimestampMixin):
    __tablename__ = "comunicados"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    autor_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[CategoriaComunicado] = mapped_column(
        SAEnum(CategoriaComunicado, name="categoria_comunicado"),
        nullable=False,
        default=CategoriaComunicado.GERAL,
        index=True,
    )
    fixado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    autor: Mapped["Usuario"] = relationship(foreign_keys=[autor_id])
    leituras: Mapped[list["LeituraComunicado"]] = relationship(
        back_populates="comunicado", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Comunicado {self.id} {self.titulo!r}>"


class LeituraComunicado(Base):
    """Marca que um morador leu o comunicado (seção 11.6.4)."""

    __tablename__ = "leituras_comunicado"
    __table_args__ = (
        UniqueConstraint("comunicado_id", "usuario_id", name="uq_leitura_por_usuario"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    comunicado_id: Mapped[int] = mapped_column(
        ForeignKey("comunicados.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    comunicado: Mapped["Comunicado"] = relationship(back_populates="leituras")
