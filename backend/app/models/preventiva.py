"""Manutenção preventiva e obrigações com vencimento.

O que vence de tempos em tempos e não pode passar: o AVCB, a recarga
dos extintores, a limpeza da caixa d'água, a manutenção dos elevadores,
a inspeção do para-raios, o seguro do condomínio. Cada plano tem a
periodicidade e o próximo vencimento; registrar a realização renova o
prazo. Remover é inativar (InativacaoMixin).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import InativacaoMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class PlanoManutencao(Base, TimestampMixin, InativacaoMixin):
    __tablename__ = "planos_manutencao"
    __table_args__ = (
        CheckConstraint("periodicidade_meses BETWEEN 1 AND 120",
                        name="ck_plano_manutencao_periodicidade"),
        CheckConstraint("antecedencia_aviso_dias BETWEEN 0 AND 180",
                        name="ck_plano_manutencao_antecedencia"),
        # Dois planos ativos com o mesmo nome confundem o painel; o
        # removido libera o nome.
        Index("uq_plano_manutencao_nome", "condominio_id", text("lower(nome)"), unique=True,
              postgresql_where=text("inativo_em IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    periodicidade_meses: Mapped[int] = mapped_column(Integer, nullable=False)
    proximo_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    # Quantos dias antes o painel começa a avisar.
    antecedencia_aviso_dias: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, server_default=text("30")
    )
    fornecedor: Mapped[str | None] = mapped_column(String(120))
    observacao: Mapped[str | None] = mapped_column(Text)
    ultima_realizacao: Mapped[date | None] = mapped_column(Date)

    realizacoes: Mapped[list["RealizacaoManutencao"]] = relationship(
        back_populates="plano", cascade="all, delete-orphan",
        order_by="(RealizacaoManutencao.data.desc(), RealizacaoManutencao.id.desc())",
    )


class RealizacaoManutencao(Base):
    """Cada vez que foi feito: o dia, o custo, e a despesa lançada com ele."""

    __tablename__ = "realizacoes_manutencao"
    __table_args__ = (
        CheckConstraint("custo IS NULL OR custo > 0", name="ck_realizacao_manutencao_custo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plano_id: Mapped[int] = mapped_column(
        ForeignKey("planos_manutencao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    custo: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    observacao: Mapped[str | None] = mapped_column(Text)
    registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    despesa_id: Mapped[int | None] = mapped_column(
        ForeignKey("despesas.id", ondelete="SET NULL")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    plano: Mapped["PlanoManutencao"] = relationship(back_populates="realizacoes")
    registrada_por: Mapped["Usuario | None"] = relationship()
