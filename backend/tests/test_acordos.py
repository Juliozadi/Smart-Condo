"""Acordo de parcelamento das cobranças vencidas.

Situação real: o apartamento deve dois meses e não consegue pagar tudo de
uma vez. O síndico fazia o acordo de boca, lançava as parcelas à mão e
precisava lembrar de dar baixa nas cobranças antigas — que continuavam
"vencidas", deixando o apartamento sem votar e sem declaração de
quitação mesmo pagando as parcelas em dia.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.api.routers import acordos as rota
from app.api.routers import financeiro as rota_financeiro
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import cab
from tests.test_financeiro import cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/financeiro"


def _mes_atras(meses: int) -> date:
    hoje = hoje_local()
    total = hoje.year * 12 + hoje.month - 1 - meses
    return date(total // 12, total % 12 + 1, 1)


def _vencida(cliente, cenario, meses_atras, dias_atraso, valor, unidade="u204"):
    """Competência de `meses_atras` meses atrás, vencida há `dias_atraso` dias."""
    r = gerar_cobranca(cliente, cenario["sindico"], cenario[unidade], valor=valor,
                       competencia=_mes_atras(meses_atras).isoformat(),
                       vencimento=(hoje_local() - timedelta(days=dias_atraso)).isoformat())
    assert r.status_code == 201, r.text
    return r.json()


def _duas_vencidas(cliente, cenario):
    a = _vencida(cliente, cenario, 3, 40, "300.00")
    b = _vencida(cliente, cenario, 2, 10, "200.00")
    return a, b


def _acordo(cliente, tok, unidade_id, ids, parcelas=3, dias=5, **extra):
    corpo = {"unidade_id": unidade_id, "cobranca_ids": ids, "parcelas": parcelas,
             "primeiro_vencimento": (hoje_local() + timedelta(days=dias)).isoformat()}
    corpo.update(extra)
    return cliente.post(f"{URL}/acordos", json=corpo, headers=cab(tok))


def _cobrancas(cliente, tok):
    return {c["id"]: c for c in cliente.get(f"{URL}/cobrancas", headers=cab(tok)).json()}


def test_acordo_junta_as_vencidas_em_parcelas(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, mensagem)))
    a, b = _duas_vencidas(cliente, cenario)
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]])
    assert r.status_code == 201, r.text
    acordo = r.json()
    # 300,00 vencida há 40 dias: multa 6,00 e juros 4,00; 200,00 há 10
    # dias: multa 4,00 e juros 0,67.
    assert Decimal(acordo["principal"]) == Decimal("500.00")
    assert Decimal(acordo["encargos"]) == Decimal("14.67")
    assert Decimal(acordo["total"]) == Decimal("514.67")
    valores = [Decimal(p["valor"]) for p in acordo["lista_parcelas"]]
    assert valores == [Decimal("171.56"), Decimal("171.56"), Decimal("171.55")]
    vencimentos = [date.fromisoformat(p["vencimento"]) for p in acordo["lista_parcelas"]]
    assert vencimentos[0] == hoje_local() + timedelta(days=5)
    assert len({v.month for v in vencimentos}) == 3
    assert acordo["situacao"] == "em_dia" and acordo["pode_cancelar"]
    assert {c["status"] for c in acordo["negociadas"]} == {"negociada"}
    assert avisos[-1][0] == "ana@exemplo.com" and "3 parcelas" in avisos[-1][1]

    # O morador vê as parcelas nas cobranças e as antigas como negociadas.
    da_ana = _cobrancas(cliente, cenario["ana"])
    assert da_ana[a["id"]]["status"] == "negociada" and da_ana[a["id"]]["acordo_id"] == acordo["id"]
    parcelas = [c for c in da_ana.values() if c["origem"] == "acordo"]
    assert len(parcelas) == 3 and all(p["acordo_id"] == acordo["id"] for p in parcelas)
    # Não está mais em atraso: as negociadas não contam.
    resumo = cliente.get(f"{URL}/resumo", headers=cab(cenario["sindico"])).json()
    assert resumo["unidades_inadimplentes"] == 0
    assert Decimal(resumo["total_aberto"]) == Decimal("514.67")


def test_em_dia_com_o_acordo_emite_a_declaracao(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    r = cliente.post("/api/v1/declaracoes-quitacao", json={}, headers=cab(cenario["ana"]))
    assert r.status_code == 409
    assert _acordo(cliente, cenario["sindico"], cenario["u204"],
                   [a["id"], b["id"]]).status_code == 201
    r = cliente.post("/api/v1/declaracoes-quitacao", json={}, headers=cab(cenario["ana"]))
    assert r.status_code in (200, 201), r.text


def test_sindico_dispensa_multa_e_juros(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]], parcelas=2,
                dispensar_encargos=True, observacao="Acordo na reunião de 10/11.")
    assert r.status_code == 201, r.text
    acordo = r.json()
    assert Decimal(acordo["encargos"]) == 0 and Decimal(acordo["total"]) == Decimal("500.00")
    assert acordo["dispensou_encargos"] and acordo["observacao"].startswith("Acordo")
    assert [p["valor"] for p in acordo["lista_parcelas"]] == ["250.00", "250.00"]


def test_o_que_ja_foi_pago_sai_do_acordo(cliente, cenario):
    a = _vencida(cliente, cenario, 3, 40, "300.00")
    # 100,00 pagos: 10,00 cobrem a multa e os juros, 90,00 abatem o valor.
    r = cliente.post(f"{URL}/cobrancas/{a['id']}/pagamentos", headers=cab(cenario["ana"]),
                     json={"valor": "100.00", "forma": "pix"})
    assert r.status_code == 201, r.text
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"]], parcelas=1,
                     dispensar_encargos=True).json()
    assert Decimal(acordo["principal"]) == Decimal("210.00")


@pytest.mark.parametrize("ajuste, codigo", [
    ({"parcelas": 0}, 422),
    ({"parcelas": 25}, 422),
    ({"dias": -1}, 422),
    ({"dias": 91}, 422),
    ({"repetir": True}, 422),
])
def test_dados_invalidos(cliente, cenario, ajuste, codigo):
    a, b = _duas_vencidas(cliente, cenario)
    ids = [a["id"], a["id"]] if ajuste.pop("repetir", False) else [a["id"], b["id"]]
    assert _acordo(cliente, cenario["sindico"], cenario["u204"], ids,
                   **ajuste).status_code == codigo


def test_so_entram_vencidas_em_aberto_do_apartamento(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    futura = gerar_cobranca(cliente, cenario["sindico"], cenario["u204"],
                            competencia=_mes_atras(0).isoformat()).json()
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], futura["id"]])
    assert r.status_code == 409 and "ainda não venceu" in r.json()["detalhe"]
    do_bruno = _vencida(cliente, cenario, 3, 40, "300.00", unidade="u301")
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], do_bruno["id"]])
    assert r.status_code == 404
    assert _acordo(cliente, cenario["sindico"], cenario["u204"], [999999]).status_code == 404
    # A que já entrou num acordo não entra em outro.
    assert _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"]]).status_code == 201
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]])
    assert r.status_code == 409 and "não está em aberto" in r.json()["detalhe"]


def test_parcela_minima(cliente, cenario):
    a = _vencida(cliente, cenario, 3, 40, "50.00")
    r = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"]], parcelas=24)
    assert r.status_code == 400 and "menos parcelas" in r.json()["detalhe"]


def test_negociada_nao_se_paga_nem_corrige(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]]).json()
    r = cliente.post(f"{URL}/cobrancas/{a['id']}/pagamentos", headers=cab(cenario["ana"]),
                     json={"valor": "300.00", "forma": "pix"})
    assert r.status_code == 409 and f"acordo nº {acordo['id']}" in r.json()["detalhe"]
    r = cliente.put(f"{URL}/cobrancas/{a['id']}", json={"valor": "10.00"},
                    headers=cab(cenario["sindico"]))
    assert r.status_code == 409


def test_parcela_atrasada_tem_multa_e_juros(cliente, cenario, monkeypatch):
    a, b = _duas_vencidas(cliente, cenario)
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]],
                     parcelas=2, dias=0, dispensar_encargos=True).json()
    primeira = acordo["lista_parcelas"][0]
    depois = hoje_local() + timedelta(days=15)
    monkeypatch.setattr(rota_financeiro, "_hoje", lambda: depois)
    monkeypatch.setattr(rota, "_hoje", lambda: depois)
    parcela = _cobrancas(cliente, cenario["ana"])[primeira["id"]]
    assert parcela["status"] == "vencida" and parcela["dias_atraso"] == 15
    assert Decimal(parcela["multa"]) == Decimal("5.00")      # 2% de 250,00
    situacao = cliente.get(f"{URL}/acordos", headers=cab(cenario["sindico"])).json()[0]["situacao"]
    assert situacao == "em_atraso"


def test_desfazer_antes_de_qualquer_pagamento(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]]).json()
    url = f"{URL}/acordos/{acordo['id']}/cancelamento"
    assert cliente.post(url, json={}, headers=cab(cenario["sindico"])).status_code == 422
    r = cliente.post(url, json={"motivo": "Parcelas lançadas no apartamento errado."},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    assert r.json()["situacao"] == "cancelado" and not r.json()["pode_cancelar"]
    cobrancas = _cobrancas(cliente, cenario["sindico"])
    assert cobrancas[a["id"]]["status"] == "vencida" and cobrancas[b["id"]]["status"] == "vencida"
    assert {p["status"] for p in r.json()["lista_parcelas"]} == {"cancelada"}
    # O histórico da cobrança mostra o que aconteceu.
    assert "desfeito" in cobrancas[a["id"]]["ultima_alteracao"]["descricao"]
    assert cliente.post(url, json={"motivo": "De novo."},
                        headers=cab(cenario["sindico"])).status_code == 409
    # As cobranças voltaram a ser devidas: entram num acordo novo.
    assert _acordo(cliente, cenario["sindico"], cenario["u204"],
                   [a["id"], b["id"]]).status_code == 201


def test_com_parcela_paga_nao_desfaz_e_quita_no_fim(cliente, cenario):
    a = _vencida(cliente, cenario, 3, 40, "300.00")
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"]], parcelas=2,
                     dispensar_encargos=True).json()
    for p in acordo["lista_parcelas"]:
        r = cliente.post(f"{URL}/cobrancas/{p['id']}/pagamentos", headers=cab(cenario["ana"]),
                         json={"valor": p["valor"], "forma": "pix"})
        assert r.status_code == 201, r.text
        r = cliente.post(f"{URL}/acordos/{acordo['id']}/cancelamento",
                         json={"motivo": "Quero desfazer."}, headers=cab(cenario["sindico"]))
        assert r.status_code == 409 and "parcela paga" in r.json()["detalhe"]
    vista = cliente.get(f"{URL}/acordos", headers=cab(cenario["ana"])).json()[0]
    assert vista["situacao"] == "quitado" and not vista["pode_cancelar"]


def test_quem_pode(cliente, cenario):
    a, b = _duas_vencidas(cliente, cenario)
    assert _acordo(cliente, cenario["ana"], cenario["u204"], [a["id"]]).status_code == 403
    assert _acordo(cliente, cenario["porteiro"], cenario["u204"], [a["id"]]).status_code == 403
    acordo = _acordo(cliente, cenario["sindico"], cenario["u204"], [a["id"], b["id"]]).json()
    assert cliente.get(f"{URL}/acordos", headers=cab(cenario["porteiro"])).status_code == 403
    assert [x["id"] for x in cliente.get(f"{URL}/acordos",
                                         headers=cab(cenario["ana"])).json()] == [acordo["id"]]
    assert cliente.get(f"{URL}/acordos", headers=cab(cenario["bruno"])).json() == []
    # O morador não desfaz o acordo.
    assert cliente.post(f"{URL}/acordos/{acordo['id']}/cancelamento",
                        json={"motivo": "Não quero mais."},
                        headers=cab(cenario["ana"])).status_code == 403
