"""Requisições que chegam ao mesmo tempo.

A conferência ("o horário está livre?", "quanto falta pagar?") e a
gravação não são um passo só. Sem trava, duas requisições simultâneas
passam juntas pela conferência: o mesmo espaço ficava reservado duas
vezes no mesmo horário, e a mesma cobrança podia ser paga a mais. Estes
testes disparam as requisições em paralelo, contra o banco de verdade.
"""
from __future__ import annotations

import threading
from datetime import date, timedelta

from tests.fixtures import cab, cadastrar_morador, CPFS
from tests.test_financeiro import gerar_cobranca
from tests.test_reservas import cenario, reservar  # noqa: F401


def ao_mesmo_tempo(n, acao):
    """Roda acao(i) em n threads, soltas juntas por uma barreira."""
    barreira = threading.Barrier(n)
    respostas = [None] * n

    def rodar(i):
        barreira.wait()
        respostas[i] = acao(i)

    threads = [threading.Thread(target=rodar, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return respostas


def test_mesmo_horario_so_uma_reserva_passa(cliente, cenario):
    _, tok_carla = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"],
        email="carla@exemplo.com", cpf=CPFS[4], unidade="402",
    )
    _, tok_davi = cadastrar_morador(
        cliente, cenario["sindico"], cenario["cond"],
        email="davi@exemplo.com", cpf=CPFS[5], unidade="503",
    )
    moradores = [cenario["ana"], cenario["bruno"], tok_carla, tok_davi]
    salao = cenario["salao"]["id"]

    for dias in range(10, 16):
        dia = (date.today() + timedelta(days=dias)).isoformat()
        codigos = ao_mesmo_tempo(4, lambda i: reservar(
            cliente, moradores[i], salao, data=dia).status_code)
        assert sorted(codigos) == [201, 409, 409, 409], (dia, codigos)


def test_mesma_cobranca_nao_e_paga_a_mais(cliente, cenario):
    unidade = cliente.get(
        "/api/v1/condominios/meu/unidades", headers=cab(cenario["sindico"])
    ).json()[0]["id"]
    cobranca = gerar_cobranca(cliente, cenario["sindico"], unidade, valor="320.00").json()

    codigos = ao_mesmo_tempo(6, lambda i: cliente.post(
        f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
        json={"valor": "200.00", "forma": "pix"}, headers=cab(cenario["sindico"]),
    ).status_code)
    # O primeiro paga 200; dos 120 que faltam, nenhum outro de 200 cabe.
    assert codigos.count(201) == 1, codigos

    pagamentos = cliente.get(
        f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
        headers=cab(cenario["sindico"]),
    ).json()
    assert sum(float(p["valor"]) for p in pagamentos) == 200.0


def test_marcar_como_lido_ao_mesmo_tempo(cliente, cenario):
    comunicado = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "Aviso geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    ).json()
    codigos = ao_mesmo_tempo(6, lambda i: cliente.post(
        f"/api/v1/comunicados/{comunicado['id']}/leitura", headers=cab(cenario["ana"]),
    ).status_code)
    assert codigos == [200] * 6


def test_registro_duplicado_ao_mesmo_tempo_e_conflito(cliente, cenario):
    """A restrição de unicidade do banco barra o segundo; a resposta é 409,
    e não um erro do servidor."""
    unidade = cliente.get(
        "/api/v1/condominios/meu/unidades", headers=cab(cenario["sindico"])
    ).json()[0]["id"]
    codigos = ao_mesmo_tempo(6, lambda i: gerar_cobranca(
        cliente, cenario["sindico"], unidade).status_code)
    assert codigos.count(201) == 1, codigos
    assert set(codigos) <= {201, 409}, codigos
