"""Schemas do financeiro.

Documentação, seção 6 (História do Usuário):
  - morador: "gostaria que o software fizesse uma cobrança mensal na data em
    que eu escolhesse, que me desse variadas opções para formas de pagamento"
  - síndico: "quando o pagamento for efetuado, o próprio sistema me notificar
    com qual meio o pagamento foi realizado, por quem e a data do pagamento"
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.models.enums import FormaPagamento, StatusCobranca
from app.schemas.comuns import SchemaBase


class PreferenciaCobrancaEntrada(SchemaBase):
    # Até 28 para o dia existir em todos os meses.
    dia_vencimento: int = Field(default=10, ge=1, le=28)
    forma_preferida: FormaPagamento = FormaPagamento.BOLETO


class PreferenciaCobrancaSaida(PreferenciaCobrancaEntrada):
    morador_id: int


class CobrancaEntrada(SchemaBase):
    unidade_id: int
    competencia: date = Field(description="Primeiro dia do mês de referência.")
    descricao: str = Field(min_length=3, max_length=180)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    vencimento: date | None = Field(
        default=None,
        description="Se ficar vazio, usa o dia escolhido pelo morador.",
    )

    @model_validator(mode="after")
    def conferir_datas(self) -> "CobrancaEntrada":
        hoje = date.today()
        competencia = self.competencia.replace(day=1)
        # Cobrança condominial prescreve em 5 anos (Código Civil, art. 206,
        # § 5º, I); mais de um ano à frente é quase sempre ano digitado errado.
        if competencia < date(hoje.year - 5, hoje.month, 1):
            raise ValueError("A competência não pode ser de mais de 5 anos atrás.")
        limite = date(hoje.year + 1, hoje.month, 1)
        if competencia > limite:
            raise ValueError("A competência não pode passar de 12 meses à frente.")
        if self.vencimento is not None and self.vencimento < competencia:
            raise ValueError("O vencimento não pode ser antes do mês de competência.")
        return self


class CobrancaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    competencia: date
    descricao: str
    valor: Decimal
    vencimento: date
    status: StatusCobranca
    total_pago: Decimal
    criado_em: datetime


class PagamentoEntrada(SchemaBase):
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    forma: FormaPagamento
    comprovante_url: str | None = Field(default=None, max_length=500)
    observacao: str | None = Field(default=None, max_length=500)


class PagamentoSaida(SchemaBase):
    id: int
    cobranca_id: int
    valor: Decimal
    forma: FormaPagamento
    pago_em: datetime
    pago_por_id: int | None = None
    pago_por_nome: str | None = None
    comprovante_url: str | None = None
    observacao: str | None = None


class ResumoFinanceiro(SchemaBase):
    """Alimenta os indicadores do painel do síndico."""
    total_aberto: Decimal
    total_vencido: Decimal
    total_recebido: Decimal
    cobrancas_abertas: int
    unidades_inadimplentes: int
