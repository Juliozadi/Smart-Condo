"""Chaves guardadas na portaria.

A chave do salão, da piscina, da casa de máquinas — e a do apartamento
que o morador deixa para a diarista ou para o eletricista. Cada retirada
fica registrada: quem levou, quando, quem entregou e quem recebeu de
volta. Uma chave só pode estar fora uma vez (restrição no banco).
Remover a chave do quadro é inativar (InativacaoMixin).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import InativacaoMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Chave(Base, TimestampMixin, InativacaoMixin):
    __tablename__ = "chaves"
    __table_args__ = (
        Index("uq_chave_nome", "condominio_id", text("lower(nome)"), unique=True,
              postgresql_where=text("inativo_em IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Vazio: chave de área comum. Preenchido: a chave que o morador deixou,
    # que só sai para quem mora lá ou para quem ele autorizou.
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    # Onde fica no quadro de chaves (o claviculário): "A3".
    posicao: Mapped[str | None] = mapped_column(String(20))
    observacao: Mapped[str | None] = mapped_column(String(300))

    unidade: Mapped["Unidade | None"] = relationship()


class MovimentacaoChave(Base):
    """Uma retirada e a devolução dela."""

    __tablename__ = "movimentacoes_chave"
    __table_args__ = (
        # A chave que está fora não sai de novo antes de voltar.
        Index("uq_chave_fora", "chave_id", unique=True,
              postgresql_where=text("devolvida_em IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chave_id: Mapped[int] = mapped_column(
        ForeignKey("chaves.id", ondelete="CASCADE"), nullable=False, index=True
    )
    retirada_por_nome: Mapped[str] = mapped_column(String(160), nullable=False)
    retirada_por_documento: Mapped[str | None] = mapped_column(String(20))
    # Quem levou a chave do apartamento: um morador de lá, ou alguém que
    # ele autorizou (autorizacoes_visita com pode_retirar_chave).
    morador_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    autorizacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("autorizacoes_visita.id", ondelete="SET NULL")
    )
    retirada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    retirada_registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    devolvida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    devolucao_registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    observacao: Mapped[str | None] = mapped_column(String(300))

    chave: Mapped["Chave"] = relationship()
    retirada_registrada_por: Mapped["Usuario | None"] = relationship(
        foreign_keys=[retirada_registrada_por_id])
    devolucao_registrada_por: Mapped["Usuario | None"] = relationship(
        foreign_keys=[devolucao_registrada_por_id])
