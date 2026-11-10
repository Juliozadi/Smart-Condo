"""Obras e reformas nos apartamentos.

A NBR 16280 pede que toda reforma seja comunicada ao síndico antes de
começar, com o que será feito, o prazo e — se mexer em estrutura,
vedações ou instalações do prédio — o responsável técnico e a ART ou
RRT. Sem isso, a quebradeira começava num sábado de manhã, o porteiro
não sabia se deixava o pedreiro subir e ninguém conferia se a parede
derrubada era estrutural. O morador comunica, o síndico aprova (com as
condições do regimento) ou recusa, e a portaria vê as obras em
andamento. A entrada dos prestadores é pela autorização de visita.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Index, String, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import StatusReforma

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Reforma(Base, TimestampMixin):
    __tablename__ = "reformas"
    __table_args__ = (
        CheckConstraint("fim >= inicio", name="ck_reforma_prazo"),
        # Estrutura, vedações ou instalações: só com responsável técnico.
        CheckConstraint(
            "NOT altera_estrutura OR (responsavel_tecnico IS NOT NULL AND art_rrt IS NOT NULL)",
            name="ck_reforma_responsavel"),
        Index("ix_reformas_condominio_fim", "condominio_id", "fim"),
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

    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    empresa: Mapped[str | None] = mapped_column(String(120))
    altera_estrutura: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    responsavel_tecnico: Mapped[str | None] = mapped_column(String(160))
    # Número da ART (engenheiro, CREA) ou do RRT (arquiteto, CAU).
    art_rrt: Mapped[str | None] = mapped_column(String(40))
    inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fim: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[StatusReforma] = mapped_column(
        SAEnum(StatusReforma, name="status_reforma"),
        nullable=False, default=StatusReforma.PENDENTE, index=True,
    )
    avaliada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    avaliada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # As condições do regimento que o síndico põe na aprovação ("só das 8h
    # às 17h", "entulho em caçamba, não no corredor").
    condicoes: Mapped[str | None] = mapped_column(String(300))
    motivo_recusa: Mapped[str | None] = mapped_column(String(300))
    cancelada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unidade: Mapped["Unidade"] = relationship()
    solicitada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[solicitada_por_id])
    cancelada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[cancelada_por_id])

    def __repr__(self) -> str:
        return f"<Reforma {self.id} {self.inicio}–{self.fim} {self.status.value}>"
