"""Medição individual de água e gás.

Situação real: a leitura do hidrômetro de cada apartamento era anotada
num caderno e a conta, feita na calculadora; o vazamento só aparecia
quando a conta chegava, meses depois.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_porteiro, montar_condominio
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/consumo"


def mes(atras: int):
    """O dia 1 de `atras` meses antes do mês atual."""
    d = hoje_local().replace(day=1)
    for _ in range(atras):
        d = (d - timedelta(days=1)).replace(day=1)
    return d


def lancar(cliente, tok, atras, leituras, tipo="agua"):
    return cliente.post(f"{URL}/leituras", headers=cab(tok), json={
        "tipo": tipo, "competencia": mes(atras).isoformat(),
        "leituras": [{"unidade_id": u, "leitura": str(v), **extra}
                     for u, v, *resto in leituras for extra in [resto[0] if resto else {}]]})


def grade(cliente, tok, atras, tipo="agua"):
    r = cliente.get(f"{URL}/leituras", headers=cab(tok),
                    params={"tipo": tipo, "competencia": mes(atras).isoformat()})
    assert r.status_code == 200, r.text
    return {l["apartamento"]: l for l in r.json()}


@pytest.fixture
def com_historico(cliente, cenario):
    """Três meses de leitura no 204 e no 301: 10 m³ por mês."""
    c = cenario
    for atras, v204, v301 in [(4, 100, 500), (3, 110, 510), (2, 120, 520), (1, 130, 530)]:
        r = lancar(cliente, c["sindico"], atras, [(c["u204"], v204), (c["u301"], v301)])
        assert r.status_code == 200, r.text
    return c


def test_consumo_e_a_diferenca_para_a_leitura_anterior(cliente, com_historico):
    c = com_historico
    primeira = grade(cliente, c["sindico"], 4)["204"]
    assert primeira["leitura"] == "100.000" and primeira["consumo"] is None
    linha = grade(cliente, c["sindico"], 1)["204"]
    assert linha["consumo"] == "10.000" and linha["anterior_leitura"] == "120.000"
    assert linha["media"] == "10.000" and linha["pode_editar"] and not linha["cobrada"]
    # Os meses do meio não se editam: há leitura depois deles.
    assert not grade(cliente, c["sindico"], 2)["204"]["pode_editar"]
    r = lancar(cliente, c["sindico"], 2, [(c["u204"], 121)])
    assert r.status_code == 409 and "mês depois" in r.json()["detalhe"]


def test_leitura_menor_que_a_anterior_so_com_troca_de_medidor(cliente, com_historico):
    c = com_historico
    r = lancar(cliente, c["sindico"], 0, [(c["u204"], 5)])
    assert r.status_code == 422 and "menor que a de" in r.json()["detalhe"]
    assert "marque a troca" in r.json()["detalhe"]
    r = lancar(cliente, c["sindico"], 0, [(c["u204"], 5, {"troca_medidor": True})])
    assert r.status_code == 200, r.text
    linha = {l["apartamento"]: l for l in r.json()}["204"]
    assert linha["consumo"] == "5.000" and linha["troca_medidor"]


def test_tudo_ou_nada(cliente, com_historico):
    c = com_historico
    # O 301 está errado: o 204, que estava certo, também não grava.
    r = lancar(cliente, c["sindico"], 0, [(c["u204"], 140), (c["u301"], 1)])
    assert r.status_code == 422
    assert grade(cliente, c["sindico"], 0)["204"]["leitura"] is None


def test_consumo_acima_do_normal_avisa_o_apartamento_uma_vez(cliente, com_historico, monkeypatch):
    c = com_historico
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, titulo, mensagem)))
    r = lancar(cliente, c["sindico"], 0, [(c["u204"], 155), (c["u301"], 541)])
    assert r.status_code == 200, r.text
    linhas = {l["apartamento"]: l for l in r.json()}
    assert linhas["204"]["acima_do_normal"] and not linhas["301"]["acima_do_normal"]
    assert len(avisos) == 1 and avisos[0][0] == "ana@exemplo.com"
    assert avisos[0][1] == "Consumo de água acima do normal"
    assert "25 m³" in avisos[0][2] and "10 m³" in avisos[0][2] and "vazamento" in avisos[0][2]
    # Salvar de novo o mesmo número não avisa outra vez.
    avisos.clear()
    lancar(cliente, c["sindico"], 0, [(c["u204"], 155)])
    assert avisos == []


def test_cobranca_pela_tarifa_e_correcao_depois_de_cancelar(cliente, com_historico):
    c = com_historico
    lancar(cliente, c["sindico"], 0, [(c["u204"], "142.5"), (c["u301"], 530)])
    r = cliente.post(f"{URL}/cobrancas", headers=cab(c["sindico"]), json={
        "tipo": "agua", "competencia": mes(0).isoformat(), "tarifa": "9.8765"})
    assert r.status_code == 201, r.text
    # 12,5 m³ × 9,8765 = 123,46; o 301 não consumiu nada e fica de fora.
    assert r.json() == {"geradas": 1, "puladas": ["301"], "total": "123.46"}
    cobrancas = [x for x in cliente.get("/api/v1/financeiro/cobrancas",
                                       headers=cab(c["ana"])).json() if x["origem"] == "consumo"]
    assert len(cobrancas) == 1 and cobrancas[0]["valor"] == "123.46"
    assert cobrancas[0]["descricao"] == (f"Consumo de água {mes(0):%m/%Y}: 12,5 m³ × "
                                         "R$ 9,8765/m³")
    # De novo: ninguém é cobrado duas vezes pela mesma leitura.
    r = cliente.post(f"{URL}/cobrancas", headers=cab(c["sindico"]), json={
        "tipo": "agua", "competencia": mes(0).isoformat(), "tarifa": "9.8765"})
    assert r.json()["geradas"] == 0
    # A leitura cobrada não se corrige...
    r = lancar(cliente, c["sindico"], 0, [(c["u204"], 141)])
    assert r.status_code == 409 and "já foi cobrada" in r.json()["detalhe"]
    # ... até a cobrança ser cancelada no financeiro.
    cliente.post(f"/api/v1/financeiro/cobrancas/{cobrancas[0]['id']}/cancelamento",
                 headers=cab(c["sindico"]), json={"motivo": "Leitura errada"})
    assert lancar(cliente, c["sindico"], 0, [(c["u204"], 141)]).status_code == 200
    r = cliente.post(f"{URL}/cobrancas", headers=cab(c["sindico"]), json={
        "tipo": "agua", "competencia": mes(0).isoformat(), "tarifa": "10"})
    assert r.json()["total"] == "110.00"
    assert grade(cliente, c["sindico"], 0)["204"]["valor_cobrado"] == "110.00"


def test_cobranca_sem_leitura_no_mes(cliente, cenario):
    r = cliente.post(f"{URL}/cobrancas", headers=cab(cenario["sindico"]), json={
        "tipo": "gas", "competencia": mes(0).isoformat(), "tarifa": "5"})
    assert r.status_code == 409 and "Nenhuma leitura de gás" in r.json()["detalhe"]


def test_historico_do_morador(cliente, com_historico):
    c = com_historico
    r = cliente.get(f"{URL}/historico", params={"tipo": "agua"}, headers=cab(c["ana"]))
    assert r.status_code == 200
    assert [h["consumo"] for h in r.json()] == ["10.000", "10.000", "10.000", None]
    # A equipe informa o apartamento.
    assert cliente.get(f"{URL}/historico", params={"tipo": "agua"},
                       headers=cab(c["sindico"])).status_code == 422
    r = cliente.get(f"{URL}/historico", params={"tipo": "agua", "unidade_id": c["u301"]},
                    headers=cab(c["sindico"]))
    assert [h["leitura"] for h in r.json()][0] == "530.000"
    # Gás é outro medidor.
    assert cliente.get(f"{URL}/historico", params={"tipo": "gas"},
                       headers=cab(c["ana"])).json() == []


def test_quem_pode_o_que(cliente, cenario):
    c = cenario
    assert lancar(cliente, c["ana"], 0, [(c["u204"], 1)]).status_code == 403
    # O porteiro só com a permissão de leituras, que o síndico libera.
    assert lancar(cliente, c["porteiro"], 0, [(c["u204"], 1)]).status_code == 403
    assert cliente.get(f"{URL}/leituras", params={"tipo": "agua", "competencia": mes(0).isoformat()},
                       headers=cab(c["porteiro"])).status_code == 403
    _, tok = cadastrar_porteiro(
        cliente, c["sindico"], c["cond"], email="zelador@exemplo.com", cpf=CPFS[4],
        permissoes={"registrar_visitantes": True, "registrar_encomendas": True,
                    "registrar_veiculos": True, "registrar_ocorrencias": True,
                    "registrar_leituras": True})
    assert lancar(cliente, tok, 0, [(c["u204"], 1)]).status_code == 200
    # Lançar a leitura, sim; cobrar, só o síndico.
    assert cliente.post(f"{URL}/cobrancas", headers=cab(tok), json={
        "tipo": "agua", "competencia": mes(0).isoformat(), "tarifa": "5"}).status_code == 403


@pytest.mark.parametrize("corpo", [
    {"competencia": "futuro"},
    {"leitura": "-1"},
    {"leitura": "12.3456"},
    {"leitura": "100000000"},
    {"repetida": True},
])
def test_dados_invalidos(cliente, cenario, corpo):
    competencia = mes(0)
    if corpo.get("competencia") == "futuro":
        competencia = (hoje_local().replace(day=28) + timedelta(days=10)).replace(day=1)
    item = {"unidade_id": cenario["u204"], "leitura": corpo.get("leitura", "10")}
    leituras = [item, item] if corpo.get("repetida") else [item]
    r = cliente.post(f"{URL}/leituras", headers=cab(cenario["sindico"]), json={
        "tipo": "agua", "competencia": competencia.isoformat(), "leituras": leituras})
    assert r.status_code == 422


@pytest.mark.parametrize("tarifa", ["0", "-1", "1000.01", "1.23456"])
def test_tarifa_invalida(cliente, cenario, tarifa):
    r = cliente.post(f"{URL}/cobrancas", headers=cab(cenario["sindico"]), json={
        "tipo": "agua", "competencia": mes(0).isoformat(), "tarifa": tarifa})
    assert r.status_code == 422


def test_outro_condominio_nao_alcanca(cliente, db, com_historico):
    c = com_historico
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert lancar(cliente, s2, 0, [(c["u204"], 200)]).status_code == 404
    assert "204" not in grade(cliente, s2, 1)
    r = cliente.get(f"{URL}/historico", params={"tipo": "agua", "unidade_id": c["u204"]},
                    headers=cab(s2))
    assert r.json() == []
    assert cliente.post(f"{URL}/cobrancas", headers=cab(s2), json={
        "tipo": "agua", "competencia": mes(1).isoformat(), "tarifa": "5"}).status_code == 409
    assert Decimal(grade(cliente, c["sindico"], 1)["204"]["leitura"]) == Decimal("130")
