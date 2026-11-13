"""Achados e perdidos da portaria.

O guarda-chuva esquecido no salão, a chave caída na garagem, os óculos na
piscina: iam para uma gaveta da portaria, e o dono só sabia se perguntasse
ao porteiro certo. Agora a portaria registra o que achou, os moradores
veem o que está guardado e dizem "é meu", e a entrega fica registrada com
o nome de quem retirou. O que ninguém reclama, depois do prazo de guarda,
o síndico doa ou descarta, com o destino anotado.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import StatusAchado

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Achado(Base, TimestampMixin):
    __tablename__ = "achados"
    __table_args__ = (
        CheckConstraint(
            "status <> 'DEVOLVIDO' OR (devolvido_em IS NOT NULL AND entregue_a IS NOT NULL)",
            name="ck_achado_devolvido"),
        CheckConstraint(
            "status <> 'DESCARTADO' OR (descartado_em IS NOT NULL AND destino IS NOT NULL)",
            name="ck_achado_descartado"),
        Index("ix_achados_condominio_status", "condominio_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    local: Mapped[str] = mapped_column(String(120), nullable=False)
    encontrado_em: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StatusAchado] = mapped_column(
        SAEnum(StatusAchado, name="status_achado"),
        nullable=False, default=StatusAchado.GUARDADO,
    )
    # O morador que disse "é meu". Só um por vez: o segundo é avisado de
    # que outro já reclamou e procura a portaria.
    reclamado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    reclamado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    devolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    devolvido_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # O nome de quem retirou, como a portaria conferiu.
    entregue_a: Mapped[str | None] = mapped_column(String(120))
    descartado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    descartado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # "Doado ao bazar da paróquia", "Descartado: estragado".
    destino: Mapped[str | None] = mapped_column(String(300))

    registrado_por: Mapped["Usuario | None"] = relationship(foreign_keys=[registrado_por_id])
    reclamado_por: Mapped["Usuario | None"] = relationship(foreign_keys=[reclamado_por_id])
    devolvido_por: Mapped["Usuario | None"] = relationship(foreign_keys=[devolvido_por_id])
