"""Portaria: visitantes, encomendas e ocorrências.

Documentação, seção 6 (História do Usuário — porteiro e morador):
  - "ao chegar na portaria, e um indivíduo dissesse que é um convidado...
     que uma notificação seja enviada para o cliente com a foto do indivíduo
     ou gravação em tempo real (vídeo porteiro), para que ele seja
     identificado e, assim, o cliente confirme se é ou não seu convidado"
  - "o sistema poderia me notificar de entregas ou pedidos que eu fiz, assim,
     o porteiro me envia pelo sistema uma foto ou vídeo para que eu
     confirmasse a minha entrega ou pedido"
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    PrioridadeOcorrencia, StatusEncomenda, StatusOcorrencia, StatusVisitante,
)

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class Visitante(Base, TimestampMixin):
    __tablename__ = "visitantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    documento: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_visita: Mapped[str] = mapped_column(String(60), nullable=False)
    placa_veiculo: Mapped[str | None] = mapped_column(String(10))

    # Vídeo porteiro: a foto capturada na portaria e enviada ao morador.
    foto_url: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[StatusVisitante] = mapped_column(
        SAEnum(StatusVisitante, name="status_visitante"),
        nullable=False,
        default=StatusVisitante.AGUARDANDO_CONFIRMACAO,
        index=True,
    )

    entrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    saida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Resposta do morador à notificação.
    confirmado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unidade: Mapped["Unidade"] = relationship()
    registrado_por: Mapped["Usuario | None"] = relationship(foreign_keys=[registrado_por_id])

    def __repr__(self) -> str:
        return f"<Visitante {self.id} {self.nome!r} {self.status.value}>"


class Encomenda(Base, TimestampMixin):
    __tablename__ = "encomendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )

    remetente: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_volume: Mapped[str] = mapped_column(String(60), nullable=False)
    codigo_rastreio: Mapped[str | None] = mapped_column(String(60), index=True)
    observacoes: Mapped[str | None] = mapped_column(Text)

    # Foto do volume, enviada ao morador junto da notificação de chegada.
    foto_url: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[StatusEncomenda] = mapped_column(
        SAEnum(StatusEncomenda, name="status_encomenda"),
        nullable=False,
        default=StatusEncomenda.AGUARDANDO_RETIRADA,
        index=True,
    )

    recebida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retirada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    unidade: Mapped["Unidade"] = relationship()
    registrada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[registrada_por_id])

    def __repr__(self) -> str:
        return f"<Encomenda {self.id} unidade={self.unidade_id} {self.status.value}>"


class Ocorrencia(Base, TimestampMixin):
    """Chamados abertos por morador, porteiro ou síndico (seção 8)."""

    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aberta_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), index=True
    )

    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False, default="geral")
    # Onde o caso aconteceu, em texto livre: "Elevador", "Apto 204",
    # "Corredor do 2º andar". O formulário sugere opções, mas o morador
    # pode descrever um lugar que não está na lista.
    local: Mapped[str | None] = mapped_column(String(120))
    prioridade: Mapped[PrioridadeOcorrencia] = mapped_column(
        SAEnum(PrioridadeOcorrencia, name="prioridade_ocorrencia"),
        nullable=False,
        default=PrioridadeOcorrencia.NORMAL,
        index=True,
    )
    foto_url: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[StatusOcorrencia] = mapped_column(
        SAEnum(StatusOcorrencia, name="status_ocorrencia"),
        nullable=False,
        default=StatusOcorrencia.ABERTA,
        index=True,
    )
    resposta: Mapped[str | None] = mapped_column(Text)
    respondida_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    respondida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    aberta_por: Mapped["Usuario"] = relationship(foreign_keys=[aberta_por_id])

    def __repr__(self) -> str:
        return f"<Ocorrencia {self.id} {self.titulo!r} {self.status.value}>"
