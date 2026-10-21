"""Assembleia virtual: convocação, pauta e votos.

Código Civil, art. 1.354-A (Lei 14.309/2022): a assembleia pode ser
eletrônica. Cada item da pauta é votado uma vez por apartamento (art.
1.352), pelo condômino quite (art. 1.335, III); alguns pedem 2/3 dos
condôminos (arts. 1.341 e 1.351) ou unanimidade.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import InativacaoMixin, TimestampMixin
from app.models.enums import EscolhaVoto, MaioriaExigida

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Assembleia(Base, TimestampMixin, InativacaoMixin):
    """Cancelar é inativar (InativacaoMixin), com o motivo guardado."""

    __tablename__ = "assembleias"
    __table_args__ = (
        CheckConstraint("encerra_em > abre_em", name="ck_assembleia_periodo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    convocada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    # A votação fica aberta entre os dois momentos; antes, só a convocação.
    abre_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    encerra_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))

    convocada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[convocada_por_id])
    itens: Mapped[list["ItemPauta"]] = relationship(
        back_populates="assembleia", cascade="all, delete-orphan", order_by="ItemPauta.ordem"
    )

    def __repr__(self) -> str:
        return f"<Assembleia {self.id} {self.titulo!r}>"


class ItemPauta(Base):
    __tablename__ = "itens_pauta"

    id: Mapped[int] = mapped_column(primary_key=True)
    assembleia_id: Mapped[int] = mapped_column(
        ForeignKey("assembleias.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    maioria: Mapped[MaioriaExigida] = mapped_column(
        SAEnum(MaioriaExigida, name="maioria_exigida"), nullable=False,
        default=MaioriaExigida.SIMPLES,
    )

    assembleia: Mapped["Assembleia"] = relationship(back_populates="itens")


class Voto(Base):
    """Um voto por apartamento em cada item — a restrição do banco garante,
    mesmo com dois moradores votando ao mesmo tempo."""

    __tablename__ = "votos"
    __table_args__ = (
        UniqueConstraint("item_id", "unidade_id", name="uq_voto_por_unidade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("itens_pauta.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Quem votou pelo apartamento.
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    escolha: Mapped[EscolhaVoto] = mapped_column(
        SAEnum(EscolhaVoto, name="escolha_voto"), nullable=False
    )
    votado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
