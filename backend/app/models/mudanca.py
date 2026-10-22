"""Agendamento de mudança.

O caminhão chegava sem aviso, ocupava o elevador de serviço a manhã
inteira e encontrava outra mudança marcada na mesma hora. O morador
pede a data e o horário, o síndico aprova, e a portaria vê as aprovadas.
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Index, String, Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import StatusMudanca, TipoMudanca

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Mudanca(Base, TimestampMixin):
    __tablename__ = "mudancas"
    __table_args__ = (
        CheckConstraint("hora_fim > hora_inicio", name="ck_mudanca_intervalo"),
        Index("ix_mudancas_condominio_data", "condominio_id", "data"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    solicitada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    tipo: Mapped[TipoMudanca] = mapped_column(
        SAEnum(TipoMudanca, name="tipo_mudanca"), nullable=False
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(120))
    observacao: Mapped[str | None] = mapped_column(String(300))

    status: Mapped[StatusMudanca] = mapped_column(
        SAEnum(StatusMudanca, name="status_mudanca"),
        nullable=False, default=StatusMudanca.PENDENTE, index=True,
    )
    avaliada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    avaliada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_recusa: Mapped[str | None] = mapped_column(String(300))
    # O próprio morador desiste, ou o síndico cancela a já aprovada
    # (elevador quebrado, obra no hall); o motivo vai para o morador.
    cancelada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))

    unidade: Mapped["Unidade"] = relationship()
    solicitada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[solicitada_por_id])
    cancelada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[cancelada_por_id])

    def __repr__(self) -> str:
        return f"<Mudanca {self.id} {self.data} {self.status.value}>"
