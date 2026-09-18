"""Cobranças, pagamentos e preferência de cobrança do morador.

Documentação, seção 6 (História do Usuário — morador):
  "gostaria que o software fizesse uma cobrança mensal na data em que eu
   escolhesse, que me desse variadas opções para formas de pagamento"
E do síndico: "quando o pagamento for efetuado, o próprio sistema me
notificar com qual meio o pagamento foi realizado, por quem e a data".
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import FormaPagamento, StatusCobranca

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class PreferenciaCobranca(Base, TimestampMixin):
    """O dia do mês e a forma de pagamento escolhidos pelo morador."""

    __tablename__ = "preferencias_cobranca"
    __table_args__ = (
        CheckConstraint("dia_vencimento BETWEEN 1 AND 28", name="ck_dia_vencimento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    morador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # Limitado a 28 para existir em todo mês, fevereiro incluído.
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    forma_preferida: Mapped[FormaPagamento] = mapped_column(
        SAEnum(FormaPagamento, name="forma_pagamento"),
        nullable=False,
        default=FormaPagamento.BOLETO,
    )

    morador: Mapped["Usuario"] = relationship()


class Cobranca(Base, TimestampMixin):
    """Uma competência mensal de uma unidade."""

    __tablename__ = "cobrancas"
    __table_args__ = (
        UniqueConstraint("unidade_id", "competencia", name="uq_cobranca_competencia"),
        CheckConstraint("valor > 0", name="ck_cobranca_valor_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Primeiro dia do mês de referência (ex.: 2025-03-01 para março/2025).
    competencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(180), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    status: Mapped[StatusCobranca] = mapped_column(
        SAEnum(StatusCobranca, name="status_cobranca"),
        nullable=False,
        default=StatusCobranca.ABERTA,
        index=True,
    )

    unidade: Mapped["Unidade"] = relationship()
    pagamentos: Mapped[list["Pagamento"]] = relationship(
        back_populates="cobranca", cascade="all, delete-orphan"
    )

    @property
    def total_pago(self) -> Decimal:
        return sum((p.valor for p in self.pagamentos), Decimal("0.00"))

    def __repr__(self) -> str:
        return f"<Cobranca {self.id} unidade={self.unidade_id} {self.competencia} {self.status.value}>"


class Pagamento(Base, TimestampMixin):
    """Registro de um pagamento — "com qual meio, por quem e a data" (seção 6)."""

    __tablename__ = "pagamentos"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_pagamento_valor_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cobranca_id: Mapped[int] = mapped_column(
        ForeignKey("cobrancas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pago_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    forma: Mapped[FormaPagamento] = mapped_column(
        SAEnum(FormaPagamento, name="forma_pagamento"), nullable=False
    )
    pago_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comprovante_url: Mapped[str | None] = mapped_column(String(500))
    observacao: Mapped[str | None] = mapped_column(Text)

    cobranca: Mapped["Cobranca"] = relationship(back_populates="pagamentos")
    pago_por: Mapped["Usuario | None"] = relationship(foreign_keys=[pago_por_id])

    def __repr__(self) -> str:
        return f"<Pagamento {self.id} cobranca={self.cobranca_id} {self.forma.value}>"
