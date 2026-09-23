"""Mensagens entre moradores, porteiros e o síndico.

Documentação, seção 13.5.2: o síndico "pode contatá-los por chat ou
ligação de voz". A conversa é entre duas pessoas do mesmo condomínio;
quem pode falar com quem está em app/services/mensagens.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Mensagem(Base):
    __tablename__ = "mensagens"
    __table_args__ = (
        CheckConstraint("remetente_id <> destinatario_id", name="ck_mensagem_para_outra_pessoa"),
        CheckConstraint("char_length(texto) BETWEEN 1 AND 2000", name="ck_mensagem_tamanho"),
        # As duas consultas mais frequentes: a conversa entre duas pessoas,
        # em ordem, e as não lidas de alguém (o contador do topo).
        Index("ix_mensagens_conversa", "remetente_id", "destinatario_id", "id"),
        Index("ix_mensagens_nao_lidas", "destinatario_id", "lida_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    remetente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    destinatario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    enviada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Mensagem {self.id} {self.remetente_id}→{self.destinatario_id}>"
