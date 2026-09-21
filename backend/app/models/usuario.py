"""Usuários, permissões do porteiro e códigos de verificação.

Documentação, seção 8 (Descrição dos Usuários) e seção 9 (casos de uso
"Cadastro", "Login do usuário", "Esqueci minha senha" e "Permissão do
Porteiro").
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    CanalVerificacao, FinalidadeCodigo, Papel, StatusUsuario, TipoOcupacao,
)

if TYPE_CHECKING:
    from app.models.condominio import Condominio, Unidade


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)

    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    data_nascimento: Mapped[date | None] = mapped_column(Date)

    senha_hash: Mapped[str] = mapped_column(String(120), nullable=False)

    papel: Mapped[Papel] = mapped_column(SAEnum(Papel, name="papel_usuario"), nullable=False)
    status: Mapped[StatusUsuario] = mapped_column(
        SAEnum(StatusUsuario, name="status_usuario"),
        nullable=False,
        default=StatusUsuario.AGUARDANDO_CODIGO,
    )

    condominio_id: Mapped[int | None] = mapped_column(
        ForeignKey("condominios.id", ondelete="SET NULL"), index=True
    )
    # Só o morador tem unidade; porteiro e síndico ficam sem.
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), index=True
    )
    tipo_ocupacao: Mapped[TipoOcupacao | None] = mapped_column(
        SAEnum(TipoOcupacao, name="tipo_ocupacao")
    )

    foto_url: Mapped[str | None] = mapped_column(String(500))

    # Quem avaliou o cadastro, quando e — na recusa — por quê. Segue a
    # mesma convenção de reservas (avaliada_por_id/avaliada_em/
    # motivo_recusa) e de ocorrências: toda decisão do sistema deixa
    # registro de autoria. Sem isso não há como responder "quem liberou
    # o acesso deste morador?", que é a decisão mais sensível de todas.
    avaliado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    avaliado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_recusa: Mapped[str | None] = mapped_column(Text)

    # Senhas erradas seguidas. Fica no banco, e não em memória, para o
    # contador sobreviver ao reinício do servidor e valer para todos os
    # processos — o mesmo motivo pelo qual codigos_verificacao já conta
    # as tentativas por aqui.
    tentativas_login: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    condominio: Mapped["Condominio | None"] = relationship(
        back_populates="usuarios", foreign_keys=[condominio_id]
    )
    unidade: Mapped["Unidade | None"] = relationship(
        back_populates="moradores", foreign_keys=[unidade_id]
    )
    permissoes: Mapped["PermissaoPorteiro | None"] = relationship(
        back_populates="porteiro",
        cascade="all, delete-orphan",
        uselist=False,
        foreign_keys="PermissaoPorteiro.porteiro_id",
    )

    @property
    def ativo(self) -> bool:
        return self.status == StatusUsuario.ATIVO

    def __repr__(self) -> str:
        return f"<Usuario {self.id} {self.email!r} {self.papel.value}>"


class PermissaoPorteiro(Base, TimestampMixin):
    """Documentação, seção 9 — caso de uso "Permissão do Porteiro":
    "o sistema mostra as possibilidades de ações do porteiro" e
    "o síndico escolhe quais estarão disponíveis para o porteiro".
    """

    __tablename__ = "permissoes_porteiro"

    id: Mapped[int] = mapped_column(primary_key=True)
    porteiro_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    registrar_visitantes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registrar_encomendas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registrar_veiculos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registrar_ocorrencias: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # O financeiro é do síndico; por padrão o porteiro não acessa.
    acessar_financeiro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    definidas_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    porteiro: Mapped["Usuario"] = relationship(
        back_populates="permissoes", foreign_keys=[porteiro_id]
    )

    def como_dicionario(self) -> dict[str, bool]:
        return {
            "registrar_visitantes": self.registrar_visitantes,
            "registrar_encomendas": self.registrar_encomendas,
            "registrar_veiculos": self.registrar_veiculos,
            "registrar_ocorrencias": self.registrar_ocorrencias,
            "acessar_financeiro": self.acessar_financeiro,
        }


class CodigoVerificacao(Base, TimestampMixin):
    """Código enviado por e-mail ou SMS.

    Documentação, seção 9: no cadastro "o sistema salva e envia um código de
    confirmação pelo meio escolhido"; em "Esqueci minha senha", "o sistema
    envia um código pelo meio escolhido pelo usuário".

    O código nunca é guardado em texto puro — apenas o hash.
    """

    __tablename__ = "codigos_verificacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    codigo_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    finalidade: Mapped[FinalidadeCodigo] = mapped_column(
        SAEnum(FinalidadeCodigo, name="finalidade_codigo"), nullable=False
    )
    canal: Mapped[CanalVerificacao] = mapped_column(
        SAEnum(CanalVerificacao, name="canal_verificacao"), nullable=False
    )

    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Registro do envio, útil enquanto não há integração real de e-mail/SMS.
    destino: Mapped[str | None] = mapped_column(Text)

    usuario: Mapped["Usuario"] = relationship()

    def __repr__(self) -> str:
        return f"<CodigoVerificacao {self.id} usuario={self.usuario_id} {self.finalidade.value}>"
