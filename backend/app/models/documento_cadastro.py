"""Documentos enviados pelo morador no cadastro.

Documentação, seção 13.3: o cadastro do morador pede RG ou CNH,
comprovante de residência e, para o proprietário, a escritura. O síndico
confere esses arquivos antes de aprovar (seção 13.5.1).

São dados pessoais sensíveis. O arquivo fica em uploads/documentos, fora
de qualquer rota pública, e só o síndico do condomínio o abre. Se o
cadastro é recusado ou o usuário é inativado, os arquivos são apagados:
não há mais finalidade para guardá-los (LGPD, art. 6º, III).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoDocumentoCadastro


class DocumentoCadastro(Base):
    __tablename__ = "documentos_cadastro"
    __table_args__ = (
        # Um arquivo por tipo: enviar de novo substitui o anterior.
        UniqueConstraint("usuario_id", "tipo", name="uq_documento_cadastro_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoDocumentoCadastro] = mapped_column(
        SAEnum(TipoDocumentoCadastro, name="tipo_documento_cadastro"), nullable=False
    )
    # Nome aleatório gravado em uploads/documentos; nunca o nome original.
    arquivo: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_conteudo: Mapped[str] = mapped_column(String(40), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    enviado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<DocumentoCadastro {self.id} usuario={self.usuario_id} {self.tipo.value}>"
