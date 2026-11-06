"""Valores escritos como o morador lê, nos avisos e nas mensagens de erro."""
from __future__ import annotations

from decimal import Decimal


def reais(valor: Decimal | int | float) -> str:
    """"R$ 1.234,56": vírgula nos centavos, ponto nos milhares."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
