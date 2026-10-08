"""Schemas de veículos, ordens de serviço e documentos."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.models.enums import (
    CategoriaDocumento, CategoriaVeiculo, PrioridadeOrdemServico, StatusOrdemServico,
    TipoMovimentacao,
)
from app.schemas.comuns import Placa, SchemaBase


# ── Veículos ─────────────────────────────────────────────────────────
class MovimentacaoEntrada(SchemaBase):
    placa: Placa
    tipo: TipoMovimentacao
    categoria: CategoriaVeiculo
    unidade_id: int | None = None
    modelo: str | None = Field(default=None, max_length=60)
    cor: str | None = Field(default=None, max_length=30)
    observacao: str | None = Field(default=None, max_length=500)


class MovimentacaoSaida(SchemaBase):
    id: int
    placa: str
    tipo: TipoMovimentacao
    categoria: CategoriaVeiculo
    unidade_id: int | None = None
    unidade: str | None = None
    modelo: str | None = None
    cor: str | None = None
    observacao: str | None = None
    registrada_em: datetime


class VeiculoNoPatio(SchemaBase):
    """Veículo cuja última movimentação foi uma entrada."""
    placa: str
    categoria: CategoriaVeiculo
    unidade: str | None = None
    modelo: str | None = None
    cor: str | None = None
    desde: datetime


class OcupacaoEstacionamento(SchemaBase):
    vagas_totais: int
    ocupadas: int
    livres: int
    percentual: int


# ── Ordens de serviço ────────────────────────────────────────────────
class OrdemServicoEntrada(SchemaBase):
    tipo: str = Field(min_length=3, max_length=60)
    descricao: str = Field(min_length=5, max_length=4000)
    local: str | None = Field(default=None, max_length=120)
    prioridade: PrioridadeOrdemServico = PrioridadeOrdemServico.MEDIA
    fornecedor: str | None = Field(default=None, max_length=120)
    data_prevista: date | None = None
    custo_estimado: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)


class OrdemServicoAtualizacao(SchemaBase):
    status: StatusOrdemServico | None = None
    prioridade: PrioridadeOrdemServico | None = None
    fornecedor: str | None = Field(default=None, max_length=120)
    data_prevista: date | None = None
    custo_estimado: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    custo_real: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    observacoes: str | None = Field(default=None, max_length=2000)


class OrdemServicoSaida(SchemaBase):
    id: int
    tipo: str
    descricao: str
    local: str | None = None
    prioridade: PrioridadeOrdemServico
    status: StatusOrdemServico
    fornecedor: str | None = None
    data_prevista: date | None = None
    custo_estimado: Decimal | None = None
    custo_real: Decimal | None = None
    observacoes: str | None = None
    aberta_por_nome: str | None = None
    concluida_em: datetime | None = None
    criado_em: datetime


class ResumoManutencao(SchemaBase):
    abertas: int
    em_andamento: int
    concluidas: int
    custo_previsto: Decimal
    custo_realizado: Decimal


# ── Documentos ───────────────────────────────────────────────────────
class DocumentoSaida(SchemaBase):
    id: int
    titulo: str
    descricao: str | None = None
    categoria: CategoriaDocumento
    # Caminho na API (/documentos/{id}/arquivo), que pede o token. Vazio
    # quando o documento não tem arquivo disponível.
    url: str | None = None
    tipo_conteudo: str | None = None
    tamanho_kb: int | None = None
    unidade: str | None = None
    publicado_por_nome: str | None = None
    publicado_em: datetime
