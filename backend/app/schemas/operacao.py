"""Schemas de veículos, ordens de serviço e documentos."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import (
    CategoriaDocumento, CategoriaVeiculo, PrioridadeOrdemServico, StatusOrdemServico,
    TipoMovimentacao,
)
from app.schemas.comuns import SchemaBase


# ── Veículos ─────────────────────────────────────────────────────────
class MovimentacaoEntrada(SchemaBase):
    placa: str = Field(min_length=7, max_length=10)
    tipo: TipoMovimentacao
    categoria: CategoriaVeiculo
    unidade_id: int | None = None
    modelo: str | None = Field(default=None, max_length=60)
    cor: str | None = Field(default=None, max_length=30)
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, valor: str) -> str:
        """Guarda só letras e números, em maiúsculas.

        Assim ABC-1D23, abc1d23 e ABC 1D23 viram a mesma placa e a consulta
        de quem está dentro não erra por causa do hífen.
        """
        limpa = "".join(c for c in valor if c.isalnum()).upper()
        if len(limpa) != 7:
            raise ValueError("A placa precisa ter 7 caracteres (ex.: ABC1D23).")
        return limpa


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
class DocumentoEntrada(SchemaBase):
    titulo: str = Field(min_length=3, max_length=180)
    descricao: str | None = Field(default=None, max_length=1000)
    categoria: CategoriaDocumento = CategoriaDocumento.OUTRO
    arquivo_url: str = Field(min_length=3, max_length=500)
    tamanho_kb: int | None = Field(default=None, ge=0)
    # Preenchido só quando o documento é de uma unidade (planta, por exemplo).
    unidade_id: int | None = None


class DocumentoSaida(SchemaBase):
    id: int
    titulo: str
    descricao: str | None = None
    categoria: CategoriaDocumento
    arquivo_url: str
    tamanho_kb: int | None = None
    unidade: str | None = None
    publicado_por_nome: str | None = None
    publicado_em: datetime
