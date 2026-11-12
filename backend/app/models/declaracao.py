"""Declaração de quitação condominial.

Na venda do apartamento, o comprador e o cartório querem a prova de que
não há taxa atrasada — a dívida de condomínio acompanha o imóvel (Código
Civil, art. 1.345). A declaração guarda o que valia no dia: o nome do
condomínio, o apartamento e o síndico daquele momento, para não mudar
depois. Não se apaga; o síndico revoga com motivo (um pagamento
estornado, por exemplo).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class DeclaracaoQuitacao(Base):
    __tablename__ = "declaracoes_quitacao"
    __table_args__ = (
        CheckConstraint("valida_ate >= referencia_ate", name="ck_declaracao_validade"),
        # Revogada tem motivo; a que vale, não.
        CheckConstraint("(revogada_em IS NULL) = (motivo_revogacao IS NULL)",
                        name="ck_declaracao_revogacao"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emitida_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    # 16 letras e números sem os que se confundem (0/O, 1/I): o que se
    # confere na verificação pública. Guardado sem os traços.
    codigo: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    # Não havia débito vencido até este dia.
    referencia_ate: Mapped[date] = mapped_column(Date, nullable=False)
    valida_ate: Mapped[date] = mapped_column(Date, nullable=False)

    # O que a declaração diz, como era no dia em que foi emitida.
    condominio_nome: Mapped[str] = mapped_column(String(160), nullable=False)
    condominio_cnpj: Mapped[str] = mapped_column(String(18), nullable=False)
    identificacao_unidade: Mapped[str] = mapped_column(String(45), nullable=False)
    sindico_nome: Mapped[str | None] = mapped_column(String(160))

    emitida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    motivo_revogacao: Mapped[str | None] = mapped_column(Text)

    unidade: Mapped["Unidade"] = relationship()
    emitida_por: Mapped["Usuario | None"] = relationship(foreign_keys=[emitida_por_id])
