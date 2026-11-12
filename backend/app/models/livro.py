"""Livro da portaria: a passagem de turno.

O caderno do balcão, no sistema: o porteiro (ou o síndico) anota o que o
próximo turno precisa saber, e quem lê dá ciência. Não se apaga nem se
edita — corrige-se com outra anotação, como no livro de papel.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class AnotacaoPortaria(Base):
    __tablename__ = "anotacoes_portaria"
    __table_args__ = (
        Index("ix_anotacoes_portaria_condominio_criado", "condominio_id", "criado_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False
    )
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    # Importante: o próximo turno precisa dar ciência.
    importante: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    autor: Mapped["Usuario | None"] = relationship()
    ciencias: Mapped[list["CienciaAnotacao"]] = relationship(
        back_populates="anotacao", cascade="all, delete-orphan", order_by="CienciaAnotacao.ciente_em"
    )


class CienciaAnotacao(Base):
    """Quem leu a anotação, e quando: uma vez por pessoa."""

    __tablename__ = "ciencias_anotacao"
    __table_args__ = (
        UniqueConstraint("anotacao_id", "usuario_id", name="uq_ciencia_anotacao"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    anotacao_id: Mapped[int] = mapped_column(
        ForeignKey("anotacoes_portaria.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    ciente_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    anotacao: Mapped["AnotacaoPortaria"] = relationship(back_populates="ciencias")
    usuario: Mapped["Usuario"] = relationship()
