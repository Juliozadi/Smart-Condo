"""Portaria: respostas dadas ao mesmo tempo, pelas duas pontas.

O morador responde pelo celular enquanto outra aba (ou outro morador da
mesma unidade) responde também; só a primeira resposta vale.
"""
from __future__ import annotations

from tests.fixtures import cab
from tests.test_concorrencia import ao_mesmo_tempo
from tests.test_portaria import cenario, registrar_encomenda, registrar_visitante  # noqa: F401


def test_visitante_liberado_e_recusado_ao_mesmo_tempo(cliente, cenario):
    for _ in range(4):
        v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
        codigos = ao_mesmo_tempo(4, lambda i, vid=v["id"]: cliente.post(
            f"/api/v1/portaria/visitantes/{vid}/confirmacao",
            json={"confirmado": i % 2 == 0}, headers=cab(cenario["ana"]),
        ).status_code)
        assert sorted(codigos) == [200, 409, 409, 409], codigos


def test_retirada_registrada_uma_vez(cliente, cenario):
    for _ in range(4):
        e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
        codigos = ao_mesmo_tempo(4, lambda i, eid=e["id"]: cliente.post(
            f"/api/v1/portaria/encomendas/{eid}/retirada",
            json={"confirmada": True}, headers=cab(cenario["ana"]),
        ).status_code)
        assert sorted(codigos) == [200, 409, 409, 409], codigos
