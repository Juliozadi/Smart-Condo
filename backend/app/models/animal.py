"""Animais de estimação dos apartamentos.

O regimento costuma pedir o cadastro dos animais e a carteira da vacina
antirrábica em dia; o síndico não tinha como saber quais apartamentos têm
animal, e a portaria, diante de um cachorro solto na garagem, não sabia de
quem era. O morador cadastra os animais do apartamento; o síndico vê
todos e lembra quem está com a vacina vencida; a portaria consulta.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import InativacaoMixin, TimestampMixin
from app.models.enums import EspecieAnimal, PorteAnimal

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Animal(Base, TimestampMixin, InativacaoMixin):
    __tablename__ = "animais"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Quem cadastrou: o morador (o animal sai da lista se ele se mudar) ou
    # o síndico.
    cadastrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    especie: Mapped[EspecieAnimal] = mapped_column(
        SAEnum(EspecieAnimal, name="especie_animal"), nullable=False)
    raca: Mapped[str | None] = mapped_column(String(60))
    porte: Mapped[PorteAnimal] = mapped_column(SAEnum(PorteAnimal, name="porte_animal"),
                                               nullable=False)
    cor: Mapped[str | None] = mapped_column(String(40))
    vacina_antirrabica_ate: Mapped[date | None] = mapped_column(Date)
    # "Bravo com outros cães: usar focinheira", "Foge pelo portão".
    observacao: Mapped[str | None] = mapped_column(String(300))
    # O último lembrete da vacina, para não mandar outro na mesma semana.
    lembrete_vacina_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unidade: Mapped["Unidade"] = relationship()
    cadastrado_por: Mapped["Usuario | None"] = relationship(foreign_keys=[cadastrado_por_id])
