"""Multa e juros da cobrança paga com atraso.

Código Civil, art. 1.336, § 1º: o condômino que não paga a contribuição
fica sujeito aos juros convencionados ou, não sendo previstos, aos de 1%
ao mês, e à multa de até 2% sobre o débito. Cada condomínio define os
seus percentuais (Condominio.multa_atraso e juros_mensais), até esses
limites.

A conta é feita sobre o que ainda falta do valor da cobrança, no dia do
pagamento: a multa uma vez, e os juros simples, dia a dia (1% ao mês =
1/30 de 1% por dia de atraso). No pagamento parcial, o dinheiro abate
primeiro a multa e os juros (art. 354) e o resto abate o valor; assim
cada parte do débito paga a multa uma vez só, e os juros até o dia em
que foi paga.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")

# Os limites da lei, que a tela do síndico não pode passar.
MULTA_MAXIMA = Decimal("2.00")
JUROS_MAXIMOS = Decimal("1.00")


@dataclass(frozen=True)
class Encargos:
    dias_atraso: int
    multa: Decimal
    juros: Decimal

    @property
    def total(self) -> Decimal:
        return self.multa + self.juros


SEM_ENCARGOS = Encargos(0, ZERO, ZERO)


def _centavos(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular(restante: Decimal, vencimento: date, dia: date,
             multa_percentual: Decimal, juros_mensais: Decimal) -> Encargos:
    """Multa e juros sobre `restante` (o que falta do valor), pagos em `dia`."""
    dias = (dia - vencimento).days
    if dias <= 0 or restante <= 0:
        return SEM_ENCARGOS
    multa = _centavos(restante * multa_percentual / 100)
    juros = _centavos(restante * juros_mensais / 100 * dias / 30)
    return Encargos(dias, multa, juros)
