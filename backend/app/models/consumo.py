"""Medição individual de água e gás.

A Lei 13.312/2016 obriga a medição individualizada de água nos prédios
novos, e muitos condomínios mais antigos já têm hidrômetro e medidor de
gás por apartamento. A leitura era anotada num caderno e a conta, feita
na calculadora; o vazamento num apartamento só aparecia quando a conta
chegava. Agora a leitura de cada mês fica registrada, o consumo sai da
diferença para a anterior, o consumo fora do normal avisa o apartamento,
e a cobrança sai pela tarifa do mês.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Index, Numeric, String,
    UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import TipoConsumo

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.financeiro import Cobranca
    from app.models.usuario import Usuario


class LeituraConsumo(Base, TimestampMixin):
    __tablename__ = "leituras_consumo"
    __table_args__ = (
        UniqueConstraint("unidade_id", "tipo", "competencia", name="uq_leitura_competencia"),
        CheckConstraint("leitura >= 0", name="ck_leitura_valor"),
        CheckConstraint("consumo IS NULL OR consumo >= 0", name="ck_leitura_consumo"),
        Index("ix_leituras_condominio_competencia", "condominio_id", "tipo", "competencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoConsumo] = mapped_column(SAEnum(TipoConsumo, name="tipo_consumo"),
                                              nullable=False)
    # O mês da leitura (sempre o dia 1).
    competencia: Mapped[date] = mapped_column(Date, nullable=False)
    # O número no medidor, em m³.
    leitura: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    # A diferença para a leitura anterior; vazio na primeira leitura do
    # apartamento, que só serve de ponto de partida.
    consumo: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    # Medidor trocado: o novo começa do zero, e o consumo é a própria leitura.
    troca_medidor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,
                                                server_default=text("false"))
    # Consumo acima do dobro da média dos meses anteriores: possível vazamento.
    acima_do_normal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,
                                                  server_default=text("false"))
    observacao: Mapped[str | None] = mapped_column(String(200))
    registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # A cobrança gerada com este consumo, quando houver.
    cobranca_id: Mapped[int | None] = mapped_column(
        ForeignKey("cobrancas.id", ondelete="SET NULL"), index=True
    )

    unidade: Mapped["Unidade"] = relationship()
    registrada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[registrada_por_id])
    cobranca: Mapped["Cobranca | None"] = relationship()
