"""Espaços comuns, reservas e ocupação em tempo real.

Documentação, seção 6 (História do Usuário):
  - "meu cliente alugou a área de confraternizações... no sistema para o
     cliente, irá mostrar que está em ocupação nesta data e horário, e eu
     gostaria que não mostrasse quem alugou, para evitar conflitos"
  - "para espaços públicos dentro do condomínio, que mostre quantos
     indivíduos estão ocupando a área no momento, por exemplo
     'Piscina: 23 pessoas no momento'"
Seção 11.5.3: o síndico aprova ou recusa a reserva.
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Integer,
    String, Text, Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import StatusReserva

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class EspacoComum(Base, TimestampMixin):
    __tablename__ = "espacos_comuns"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Espaço de uso livre (piscina, academia) mostra ocupação instantânea;
    # espaço reservável (salão, churrasqueira) passa por reserva.
    reservavel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    uso_livre: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    em_manutencao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reservas: Mapped[list["Reserva"]] = relationship(
        back_populates="espaco", cascade="all, delete-orphan"
    )
    registros_ocupacao: Mapped[list["RegistroOcupacao"]] = relationship(
        back_populates="espaco", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EspacoComum {self.id} {self.nome!r}>"


class Reserva(Base, TimestampMixin):
    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint("hora_fim > hora_inicio", name="ck_reserva_intervalo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    espaco_id: Mapped[int] = mapped_column(
        ForeignKey("espacos_comuns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Quem reservou. Este campo nunca sai numa resposta para outro morador:
    # o sigilo da autoria é requisito da seção 6.
    morador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)

    pessoas_estimadas: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[StatusReserva] = mapped_column(
        SAEnum(StatusReserva, name="status_reserva"),
        nullable=False,
        default=StatusReserva.PENDENTE,
        index=True,
    )
    avaliada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    avaliada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_recusa: Mapped[str | None] = mapped_column(Text)

    espaco: Mapped["EspacoComum"] = relationship(back_populates="reservas")
    morador: Mapped["Usuario"] = relationship(foreign_keys=[morador_id])

    def __repr__(self) -> str:
        return f"<Reserva {self.id} espaco={self.espaco_id} {self.data} {self.status.value}>"


class RegistroOcupacao(Base, TimestampMixin):
    """Contagem instantânea de pessoas numa área de uso livre.

    Cada leitura é uma linha; a ocupação "agora" é a leitura mais recente.
    Guardar o histórico permite mostrar horários de pico depois.
    """

    __tablename__ = "registros_ocupacao"
    __table_args__ = (
        CheckConstraint("pessoas >= 0", name="ck_ocupacao_nao_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    espaco_id: Mapped[int] = mapped_column(
        ForeignKey("espacos_comuns.id", ondelete="CASCADE"), nullable=False, index=True
    )

    pessoas: Mapped[int] = mapped_column(Integer, nullable=False)
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    espaco: Mapped["EspacoComum"] = relationship(back_populates="registros_ocupacao")

    def __repr__(self) -> str:
        return f"<RegistroOcupacao espaco={self.espaco_id} pessoas={self.pessoas}>"
