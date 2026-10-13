"""Regras de uso de cada espaço.

Situação real: o salão funciona só até as 22h (lei do silêncio), precisa
ser reservado com dois dias de antecedência, a churrasqueira vale por no
máximo seis horas, e cada apartamento pode ter uma reserva futura de cada
espaço por vez. Nada disso existia: qualquer horário passava.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.tempo import hoje_local
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_reservas import cenario, reservar  # noqa: F401


def _dia(n):
    return (hoje_local() + timedelta(days=n)).isoformat()


def _regras(cliente, cenario, **regras):
    r = cliente.put(f"/api/v1/espacos/{cenario['salao']['id']}", headers=cab(cenario["sindico"]),
                    json=regras)
    assert r.status_code == 200, r.text
    return r.json()


def test_espaco_devolve_as_regras(cliente, cenario):
    espaco = _regras(cliente, cenario, horario_abertura="08:00", horario_fechamento="22:00",
                     antecedencia_minima_dias=2, duracao_maxima_horas=6, limite_por_unidade=1)
    assert espaco["horario_abertura"] == "08:00:00"
    assert espaco["horario_fechamento"] == "22:00:00"
    assert espaco["antecedencia_minima_dias"] == 2
    assert espaco["duracao_maxima_horas"] == 6
    assert espaco["limite_por_unidade"] == 1
    assert "o horário" in espaco["ultima_alteracao"]["descricao"]


def test_fora_do_horario_de_funcionamento(cliente, cenario):
    _regras(cliente, cenario, horario_abertura="08:00", horario_fechamento="22:00")
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="20:00", fim="23:00",
                 data=_dia(5))
    assert r.status_code == 400
    assert "08:00 às 22:00" in r.json()["detalhe"]
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="07:00", fim="09:00",
                 data=_dia(5))
    assert r.status_code == 400
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="08:00", fim="22:00",
                 data=_dia(5))
    assert r.status_code == 201, r.text


def test_antecedencia_minima(cliente, cenario):
    _regras(cliente, cenario, antecedencia_minima_dias=2)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], data=_dia(1))
    assert r.status_code == 400
    assert "2 dias de antecedência" in r.json()["detalhe"]
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"],
                    data=_dia(2)).status_code == 201


def test_duracao_maxima(cliente, cenario):
    _regras(cliente, cenario, duracao_maxima_horas=6)
    r = reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="10:00", fim="16:30",
                 data=_dia(5))
    assert r.status_code == 400
    assert "6 horas" in r.json()["detalhe"]
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="10:00",
                    fim="16:00", data=_dia(5)).status_code == 201


def test_limite_conta_o_apartamento_inteiro(cliente, cenario):
    _regras(cliente, cenario, limite_por_unidade=1)
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"],
                    data=_dia(5)).status_code == 201
    # Outro morador do mesmo apartamento também esbarra no limite.
    _, tok_vizinha = cadastrar_morador(cliente, cenario["sindico"], cenario["cond"],
                                       email="filha@exemplo.com", cpf=CPFS[4], unidade="204")
    r = reservar(cliente, tok_vizinha, cenario["salao"]["id"], data=_dia(9))
    assert r.status_code == 409
    assert "limite" in r.json()["detalhe"]
    # Outro apartamento, não.
    assert reservar(cliente, cenario["bruno"], cenario["salao"]["id"],
                    data=_dia(9)).status_code == 201


def test_cancelar_libera_o_limite(cliente, cenario):
    _regras(cliente, cenario, limite_por_unidade=1)
    primeira = reservar(cliente, cenario["ana"], cenario["salao"]["id"], data=_dia(5)).json()
    cliente.delete(f"/api/v1/espacos/reservas/{primeira['id']}", headers=cab(cenario["ana"]))
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"],
                    data=_dia(6)).status_code == 201


def test_sem_regras_tudo_continua_como_antes(cliente, cenario):
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="00:30",
                    fim="23:30", data=_dia(1)).status_code == 201


def test_tirar_a_regra(cliente, cenario):
    _regras(cliente, cenario, horario_abertura="08:00", horario_fechamento="22:00")
    espaco = _regras(cliente, cenario, horario_abertura=None, horario_fechamento=None)
    assert espaco["horario_abertura"] is None
    assert reservar(cliente, cenario["ana"], cenario["salao"]["id"], inicio="22:00",
                    fim="23:30", data=_dia(5)).status_code == 201


@pytest.mark.parametrize("regras", [
    {"horario_abertura": "22:00", "horario_fechamento": "08:00"},
    {"horario_abertura": "08:00"},
    {"antecedencia_minima_dias": -1},
    {"duracao_maxima_horas": 0},
    {"limite_por_unidade": 0},
])
def test_regras_invalidas(cliente, cenario, regras):
    r = cliente.put(f"/api/v1/espacos/{cenario['salao']['id']}", headers=cab(cenario["sindico"]),
                    json=regras)
    assert r.status_code == 422, (regras, r.text)
