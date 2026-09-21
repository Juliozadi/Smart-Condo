"""Veículos, ordens de serviço e documentos.

Três módulos que o front-end já apresenta:
  - veículos (porteiro): controle de entrada e saída no estacionamento
  - manutenção (síndico): abertura e acompanhamento de ordens de serviço
  - documentos (morador): atas, convenção e regimento interno
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    CategoriaDocumento, CategoriaVeiculo, PrioridadeOrdemServico, StatusOrdemServico,
    TipoMovimentacao,
)

if TYPE_CHECKING:
    from app.models.condominio import Unidade
    from app.models.usuario import Usuario


class MovimentacaoVeiculo(Base, TimestampMixin):
    """Uma entrada ou uma saída do estacionamento.

    Cada passagem é uma linha. Quais veículos estão dentro se descobre pela
    última movimentação de cada placa: guardar um campo "dentro" daria
    margem a ele divergir do histórico.
    """

    __tablename__ = "movimentacoes_veiculo"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    placa: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    modelo: Mapped[str | None] = mapped_column(String(60))
    cor: Mapped[str | None] = mapped_column(String(30))

    tipo: Mapped[TipoMovimentacao] = mapped_column(
        SAEnum(TipoMovimentacao, name="tipo_movimentacao"), nullable=False, index=True
    )
    categoria: Mapped[CategoriaVeiculo] = mapped_column(
        SAEnum(CategoriaVeiculo, name="categoria_veiculo"), nullable=False
    )

    # Morador tem unidade; visitante e prestador podem não ter.
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), index=True
    )
    registrada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    registrada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    observacao: Mapped[str | None] = mapped_column(Text)

    unidade: Mapped["Unidade | None"] = relationship()

    def __repr__(self) -> str:
        return f"<MovimentacaoVeiculo {self.id} {self.placa} {self.tipo.value}>"


class OrdemServico(Base, TimestampMixin):
    """Manutenção do condomínio, aberta e acompanhada pelo síndico."""

    __tablename__ = "ordens_servico"
    __table_args__ = (
        CheckConstraint("custo_estimado IS NULL OR custo_estimado >= 0",
                        name="ck_os_custo_estimado"),
        CheckConstraint("custo_real IS NULL OR custo_real >= 0", name="ck_os_custo_real"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    local: Mapped[str | None] = mapped_column(String(120))

    prioridade: Mapped[PrioridadeOrdemServico] = mapped_column(
        SAEnum(PrioridadeOrdemServico, name="prioridade_ordem_servico"),
        nullable=False,
        default=PrioridadeOrdemServico.MEDIA,
        index=True,
    )
    status: Mapped[StatusOrdemServico] = mapped_column(
        SAEnum(StatusOrdemServico, name="status_ordem_servico"),
        nullable=False,
        default=StatusOrdemServico.ABERTA,
        index=True,
    )

    fornecedor: Mapped[str | None] = mapped_column(String(120))
    data_prevista: Mapped[date | None] = mapped_column(Date)
    custo_estimado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    custo_real: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    aberta_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observacoes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<OrdemServico {self.id} {self.tipo!r} {self.status.value}>"


class Documento(Base, TimestampMixin):
    """Atas, convenção, regimento e demais arquivos do condomínio.

    A tabela guarda a URL do arquivo; o armazenamento em si fica fora do
    banco, como já acontece com as fotos da portaria.
    """

    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    condominio_id: Mapped[int] = mapped_column(
        ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, index=True
    )

    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    categoria: Mapped[CategoriaDocumento] = mapped_column(
        SAEnum(CategoriaDocumento, name="categoria_documento"),
        nullable=False,
        default=CategoriaDocumento.OUTRO,
        index=True,
    )

    arquivo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    tamanho_kb: Mapped[int | None] = mapped_column()

    # Documento de uma unidade específica (planta, por exemplo) só aparece
    # para quem mora nela; sem unidade, vale para todo o condomínio.
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), index=True
    )

    publicado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Documento {self.id} {self.titulo!r}>"
