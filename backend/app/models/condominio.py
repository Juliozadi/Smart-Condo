"""Condomínio e unidades.

Documentação, seção 9 — caso de uso "Cadastro do condomínio" (usuário
principal: síndico) — e seção 11.3, que descreve os dados da unidade do
morador: condomínio, bloco/torre e número de vagas na garagem.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Condominio(Base, TimestampMixin):
    __tablename__ = "condominios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, index=True)

    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(180), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(80))
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)

    telefone: Mapped[str | None] = mapped_column(String(20))

    # O síndico que cadastrou o condomínio (pré-requisito da seção 9:
    # "Existir um síndico ativo").
    sindico_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "usuarios.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_condominios_sindico_id",
        ),
        index=True,
    )

    unidades: Mapped[list["Unidade"]] = relationship(
        back_populates="condominio", cascade="all, delete-orphan"
    )
    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="condominio", foreign_keys="Usuario.condominio_id"
    )

    def __repr__(self) -> str:
        return f"<Condominio {self.id} {self.nome!r}>"


class Unidade(Base, TimestampMixin):
    """Um apartamento/casa do condomínio."""

    __tablename__ = "unidades"
    __table_args__ = (
        UniqueConstraint("condominio_id", "bloco", "numero", name="uq_unidade_no_condominio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    bloco: Mapped[str] = mapped_column(String(20), nullable=False, default="unico")
    andar: Mapped[int | None] = mapped_column(Integer)
    vagas_garagem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    condominio: Mapped["Condominio"] = relationship(back_populates="unidades")
    moradores: Mapped[list["Usuario"]] = relationship(
        back_populates="unidade", foreign_keys="Usuario.unidade_id"
    )

    @property
    def identificacao(self) -> str:
        return self.numero if self.bloco == "unico" else f"{self.bloco} {self.numero}"

    def __repr__(self) -> str:
        return f"<Unidade {self.id} {self.identificacao!r}>"
