"""Schemas do financeiro.

Documentação, seção 6 (História do Usuário):
  - morador: "gostaria que o software fizesse uma cobrança mensal na data em
    que eu escolhesse, que me desse variadas opções para formas de pagamento"
  - síndico: "quando o pagamento for efetuado, o próprio sistema me notificar
    com qual meio o pagamento foi realizado, por quem e a data do pagamento"
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from app.core.tempo import hoje_local
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.models.enums import CategoriaDespesa, FormaPagamento, StatusCobranca
from app.schemas.admin import RegistroSaida
from app.schemas.comuns import EnderecoWeb, SchemaBase


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
        hoje = hoje_local()
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


class CobrancaAtualizacao(SchemaBase):
    """Correção de uma cobrança lançada errada. Só o que veio muda."""
    descricao: str | None = Field(default=None, min_length=3, max_length=180)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    vencimento: date | None = None

    @model_validator(mode="after")
    def _sem_nulos(self) -> "CobrancaAtualizacao":
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"O campo {campo} não pode ficar vazio.")
        return self


class CancelamentoCobranca(SchemaBase):
    motivo: str = Field(min_length=3, max_length=300)


class CobrancaSaida(SchemaBase):
    id: int
    unidade_id: int
    unidade: str | None = None
    competencia: date
    descricao: str
    valor: Decimal
    vencimento: date
    status: StatusCobranca
    # O que já abateu do valor (sem a multa e os juros pagos).
    total_pago: Decimal
    # Paga hoje: os encargos do atraso sobre o que falta, e o total a pagar.
    dias_atraso: int = 0
    multa: Decimal = Decimal("0.00")
    juros: Decimal = Decimal("0.00")
    total_atualizado: Decimal = Decimal("0.00")
    criado_em: datetime
    # Só para o síndico: "Editado por Fulano em ...".
    ultima_alteracao: RegistroSaida | None = None


class PagamentoEntrada(SchemaBase):
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    forma: FormaPagamento
    comprovante_url: EnderecoWeb | None = None
    observacao: str | None = Field(default=None, max_length=500)
    # Só o síndico: num acordo, recebe sem a multa e os juros do atraso.
    dispensar_encargos: bool = False


class PagamentoSaida(SchemaBase):
    id: int
    cobranca_id: int
    valor: Decimal
    # Quanto do valor foi para a multa e os juros do atraso.
    encargos: Decimal = Decimal("0.00")
    forma: FormaPagamento
    pago_em: datetime
    pago_por_id: int | None = None
    pago_por_nome: str | None = None
    comprovante_url: str | None = None
    observacao: str | None = None


class EncargosCondominio(SchemaBase):
    """Multa e juros da cobrança paga com atraso, em %. Os limites são os
    do Código Civil, art. 1.336, § 1º."""
    multa_atraso: Decimal = Field(ge=0, le=2, max_digits=4, decimal_places=2)
    juros_mensais: Decimal = Field(ge=0, le=1, max_digits=4, decimal_places=2)


class ResumoFinanceiro(SchemaBase):
    """Alimenta os indicadores do painel do síndico."""
    total_aberto: Decimal
    total_vencido: Decimal
    total_recebido: Decimal
    cobrancas_abertas: int
    unidades_inadimplentes: int


# ── Prestação de contas ──────────────────────────────────────────────
def _data_da_despesa(dia: date) -> date:
    hoje = hoje_local()
    if dia > hoje:
        raise ValueError("A despesa entra quando é paga: a data não pode ser futura.")
    # Como a cobrança: contas de condomínio prescrevem em 5 anos.
    if dia < hoje - timedelta(days=5 * 366):
        raise ValueError("A data não pode ser de mais de 5 anos atrás.")
    return dia


def _vazio_e_nada(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


class DespesaEntrada(SchemaBase):
    categoria: CategoriaDespesa
    descricao: str = Field(min_length=3, max_length=180)
    valor: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    data: date
    fornecedor: str | None = Field(default=None, max_length=120)

    _fornecedor_vazio = field_validator("fornecedor", mode="before")(_vazio_e_nada)

    @field_validator("data")
    @classmethod
    def _data(cls, dia: date) -> date:
        return _data_da_despesa(dia)


class DespesaAtualizacao(SchemaBase):
    """Correção de uma despesa lançada errada. Só o que veio muda; o
    fornecedor pode ser apagado, o resto não fica vazio."""
    categoria: CategoriaDespesa | None = None
    descricao: str | None = Field(default=None, min_length=3, max_length=180)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    data: date | None = None
    fornecedor: str | None = Field(default=None, max_length=120)

    _fornecedor_vazio = field_validator("fornecedor", mode="before")(_vazio_e_nada)

    @field_validator("data")
    @classmethod
    def _data(cls, dia: date | None) -> date | None:
        return None if dia is None else _data_da_despesa(dia)

    @model_validator(mode="after")
    def _sem_nulos(self) -> "DespesaAtualizacao":
        for campo in self.model_fields_set - {"fornecedor"}:
            if getattr(self, campo) is None:
                raise ValueError(f"O campo {campo} não pode ficar vazio.")
        return self


class DespesaSaida(SchemaBase):
    id: int
    categoria: CategoriaDespesa
    descricao: str
    valor: Decimal
    data: date
    fornecedor: str | None = None
    # Caminho na API, que confere quem pode abrir. None sem comprovante.
    comprovante_url: str | None = None
    lancada_por_nome: str | None = None
    cancelada: bool = False
    criado_em: datetime
    # Só para o síndico: "Editado por Fulano em ...".
    ultima_alteracao: RegistroSaida | None = None


class TotalPorCategoria(SchemaBase):
    categoria: CategoriaDespesa
    total: Decimal


class Balancete(SchemaBase):
    """O mês do condomínio: o que entrou, o que saiu e o saldo."""
    mes: str
    # Todo o dinheiro recebido no mês, multa e juros incluídos.
    receitas: Decimal
    despesas: Decimal
    saldo_do_mes: Decimal
    # Receitas menos despesas de todos os meses anteriores.
    saldo_anterior: Decimal
    saldo_acumulado: Decimal
    por_categoria: list[TotalPorCategoria]
