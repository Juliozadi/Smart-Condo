"""Que dia é hoje e que horas são, no fuso do condomínio.

As regras de data (reserva em horário que já passou, cobrança vencida,
data de nascimento no futuro) não podem depender do relógio da máquina:
o servidor que hospeda a API costuma estar em UTC, quatro horas à frente
de Campo Grande. Todo "hoje" e "agora" da API passa por aqui.
"""
from __future__ import annotations

import calendar
import logging
from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings

logger = logging.getLogger("smartcondo")


@lru_cache
def _fuso(nome: str) -> ZoneInfo | None:
    try:
        return ZoneInfo(nome)
    except (ZoneInfoNotFoundError, ValueError):
        # Sem a base de fusos (o Windows não traz; ela vem no pacote
        # tzdata), vale o relógio da máquina — o mesmo de antes.
        logger.warning("Fuso %r indisponível; usando o relógio da máquina. "
                       "Instale o pacote tzdata.", nome)
        return None


def agora_local() -> datetime:
    """Data e hora de agora no fuso do condomínio."""
    fuso = _fuso(settings.FUSO_HORARIO)
    return datetime.now(fuso) if fuso else datetime.now().astimezone()


def hoje_local() -> date:
    """A data de hoje no fuso do condomínio."""
    return agora_local().date()


def somar_meses(dia: date, meses: int) -> date:
    """31/01 + 1 mês é 28/02 (ou 29): o dia que não existe vira o último."""
    total = dia.month - 1 + meses
    ano, mes = dia.year + total // 12, total % 12 + 1
    return date(ano, mes, min(dia.day, calendar.monthrange(ano, mes)[1]))
