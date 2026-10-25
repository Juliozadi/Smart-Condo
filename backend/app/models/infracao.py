"""Advertências e multas por infração do regimento.

Código Civil, art. 1.336, § 2º: quem descumpre os deveres do condomínio
paga a multa da convenção, até 5 vezes a contribuição mensal; art.
1.337: o reincidente. Antes da multa, o apartamento é notificado e tem
prazo para se defender — a multa sem defesa costuma cair na Justiça.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import StatusInfracao, TipoInfracao

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Infracao(Base, TimestampMixin):
    __tablename__ = "infracoes"
    __table_args__ = (
        # Advertência não tem valor; multa tem, e positivo.
        CheckConstraint("(tipo = 'MULTA' AND valor > 0) OR (tipo = 'ADVERTENCIA' AND valor IS NULL)",
                        name="ck_infracao_valor"),
        Index("ix_infracoes_unidade_criado", "unidade_id", "criado_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False
    )
    aplicada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    tipo: Mapped[TipoInfracao] = mapped_column(
        SAEnum(TipoInfracao, name="tipo_infracao"), nullable=False
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    # O artigo do regimento ou da convenção que foi descumprido.
    artigo: Mapped[str | None] = mapped_column(String(120))
    ocorrida_em: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    prazo_defesa: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[StatusInfracao] = mapped_column(
        SAEnum(StatusInfracao, name="status_infracao"),
        nullable=False, default=StatusInfracao.NOTIFICADA, index=True,
    )
    defesa: Mapped[str | None] = mapped_column(Text)
    defesa_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    defesa_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    decisao_motivo: Mapped[str | None] = mapped_column(Text)
    decidida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decidida_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # A multa mantida vira cobrança do apartamento.
    cobranca_id: Mapped[int | None] = mapped_column(
        ForeignKey("cobrancas.id", ondelete="SET NULL")
    )

    unidade: Mapped["Unidade"] = relationship()
    aplicada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[aplicada_por_id])
    defesa_por: Mapped["Usuario | None"] = relationship(foreign_keys=[defesa_por_id])

    def __repr__(self) -> str:
        return f"<Infracao {self.id} {self.tipo.value} {self.status.value}>"
