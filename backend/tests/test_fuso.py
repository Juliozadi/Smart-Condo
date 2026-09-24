"""O "hoje" da API é o do condomínio, e não o da máquina.

O servidor costuma estar em UTC, quatro horas à frente de Campo Grande.
Com o relógio da máquina, às 18h de lá a reserva das 19h seria recusada
como "horário que já passou", e uma cobrança venceria quatro horas antes.

Os testes usam dois fusos de pontas opostas: Pago Pago (UTC−11) e
Kiritimati (UTC+14). A diferença é de 25 horas, então a data de um é
sempre anterior à do outro, a qualquer hora em que a suíte rode.
"""
from __future__ import annotations

import pytest

from app.core import tempo
from app.core.config import settings
from tests.test_reservas import cenario, reservar  # noqa: F401

ATRAS = "Pacific/Pago_Pago"       # UTC−11
ADIANTE = "Pacific/Kiritimati"   # UTC+14


def hoje_em(monkeypatch, fuso):
    monkeypatch.setattr(settings, "FUSO_HORARIO", fuso)
    return tempo.hoje_local()


def test_hoje_depende_do_fuso_do_condominio(monkeypatch):
    assert hoje_em(monkeypatch, ATRAS) < hoje_em(monkeypatch, ADIANTE)


def test_fuso_inexistente_usa_o_relogio_da_maquina(monkeypatch):
    monkeypatch.setattr(settings, "FUSO_HORARIO", "Nao/Existe")
    assert tempo.agora_local().tzinfo is not None


@pytest.mark.parametrize("fuso, aceita", [(ATRAS, True), (ADIANTE, False)])
def test_reserva_usa_o_dia_do_condominio(cliente, cenario, monkeypatch, fuso, aceita):
    """Reserva para o "hoje" de Pago Pago: ainda é hoje (ou futuro) para
    um condomínio lá, e já é passado para um condomínio em Kiritimati."""
    dia = hoje_em(monkeypatch, ATRAS).isoformat()
    monkeypatch.setattr(settings, "FUSO_HORARIO", fuso)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], "23:00", "23:59", data=dia)
    if aceita:
        # Às 23h de Pago Pago o horário pode já ter passado; o que importa
        # é que a data não foi tratada como passada.
        assert r.status_code == 201 or "já passou" in r.json()["detalhe"], r.text
    else:
        assert r.status_code == 400
        assert "data passada" in r.json()["detalhe"]
