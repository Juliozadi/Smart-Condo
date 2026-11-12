"""Cobranças de todos os apartamentos de uma vez: a taxa do mês ou a cota
extra, pelo mesmo valor ou rateada pela fração ideal.

Situação real: a convenção manda ratear as despesas pela fração ideal —
a cobertura paga mais que o apartamento-tipo —, e a assembleia aprova a
pintura da fachada em seis parcelas. O síndico lançava apartamento por
apartamento, com a calculadora do lado, e um erro no meio deixava metade
do prédio cobrado.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import cab
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/financeiro"
COMPETENCIA = hoje_local().replace(day=1).isoformat()
VENCIMENTO = (hoje_local() + timedelta(days=7)).isoformat()


def lote(cliente, tok, **extra):
    corpo = {"competencia": COMPETENCIA, "descricao": "Taxa de condomínio",
             "valor": "320.00", "vencimento": VENCIMENTO}
    corpo.update(extra)
    return cliente.post(f"{URL}/cobrancas/lote", json=corpo, headers=cab(tok))


def fracao(cliente, tok, unidade_id, valor):
    return cliente.put(f"/api/v1/condominios/meu/unidades/{unidade_id}",
                       json={"fracao_ideal": valor}, headers=cab(tok))


def por_unidade(cliente, tok, origem="taxa"):
    saida = {}
    for c in cliente.get(f"{URL}/cobrancas", headers=cab(tok)).json():
        if c["origem"] == origem:
            saida.setdefault(c["unidade_id"], []).append(c)
    return saida


def test_taxa_igual_para_todos_e_quem_ja_tem_e_pulado(cliente, cenario):
    r = lote(cliente, cenario["sindico"])
    assert r.status_code == 201, r.text
    assert r.json() == {"geradas": 2, "puladas": [], "total": "640.00"}
    cobrancas = por_unidade(cliente, cenario["sindico"])
    assert {u: [c["valor"] for c in cs] for u, cs in cobrancas.items()} == {
        cenario["u204"]: ["320.00"], cenario["u301"]: ["320.00"]}
    # De novo: ninguém é cobrado duas vezes no mesmo mês.
    r = lote(cliente, cenario["sindico"])
    assert r.status_code == 201
    assert r.json()["geradas"] == 0 and len(r.json()["puladas"]) == 2


def test_rateio_pela_fracao_ideal_sem_perder_centavo(cliente, cenario):
    assert fracao(cliente, cenario["sindico"], cenario["u204"], "40").status_code == 200
    assert fracao(cliente, cenario["sindico"], cenario["u301"], "60").status_code == 200
    r = lote(cliente, cenario["sindico"], rateio="fracao", valor="1000.01")
    assert r.status_code == 201, r.text
    assert r.json()["total"] == "1000.01"
    cobrancas = por_unidade(cliente, cenario["sindico"])
    assert cobrancas[cenario["u204"]][0]["valor"] == "400.00"
    assert cobrancas[cenario["u301"]][0]["valor"] == "600.01"


def test_fracoes_incompletas_ou_que_nao_somam_100(cliente, cenario):
    fracao(cliente, cenario["sindico"], cenario["u204"], "40")
    r = lote(cliente, cenario["sindico"], rateio="fracao", valor="1000.00")
    assert r.status_code == 409 and "Faltam" in r.json()["detalhe"]
    fracao(cliente, cenario["sindico"], cenario["u301"], "50")
    r = lote(cliente, cenario["sindico"], rateio="fracao", valor="1000.00")
    assert r.status_code == 409 and "somam 90%" in r.json()["detalhe"]
    # Nada foi lançado.
    assert por_unidade(cliente, cenario["sindico"]) == {}


def test_cota_extra_em_parcelas(cliente, cenario):
    r = lote(cliente, cenario["sindico"], tipo="extra", descricao="Pintura da fachada",
             valor="300.00", parcelas=3)
    assert r.status_code == 201, r.text
    assert r.json()["geradas"] == 6 and r.json()["total"] == "600.00"
    extras = por_unidade(cliente, cenario["sindico"], origem="extra")
    do_204 = sorted(extras[cenario["u204"]], key=lambda c: c["vencimento"])
    assert [c["valor"] for c in do_204] == ["100.00", "100.00", "100.00"]
    assert do_204[0]["descricao"] == "Pintura da fachada — parcela 1/3"
    assert len({date.fromisoformat(c["vencimento"]).month for c in do_204}) == 3
    assert do_204[0]["vencimento"] == VENCIMENTO
    # A cota extra entra ao lado da taxa do mês, sem tomar o lugar dela.
    assert lote(cliente, cenario["sindico"]).json()["geradas"] == 2
    # O mesmo lançamento duas vezes, não.
    r = lote(cliente, cenario["sindico"], tipo="extra", descricao="Pintura da fachada",
             valor="300.00", parcelas=3)
    assert r.status_code == 409 and "já foi lançada" in r.json()["detalhe"]


def test_cota_extra_avisa_cada_apartamento_da_sua_parte(cliente, cenario, monkeypatch):
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(
                            (destino, titulo, mensagem)))
    # A taxa do mês é rotina: não avisa.
    assert lote(cliente, cenario["sindico"]).status_code == 201
    assert avisos == []
    fracao(cliente, cenario["sindico"], cenario["u204"], "40")
    fracao(cliente, cenario["sindico"], cenario["u301"], "60")
    r = lote(cliente, cenario["sindico"], tipo="extra", rateio="fracao",
             descricao="Troca do portão", valor="1500.00", parcelas=3)
    assert r.status_code == 201, r.text
    data = date.fromisoformat(VENCIMENTO).strftime("%d/%m/%Y")
    assert sorted(avisos) == [
        ("ana@exemplo.com", "Cota extra lançada",
         f"Troca do portão: a parte da unidade 204 é R$ 600,00, em 3 parcelas mensais, "
         f"com o primeiro vencimento em {data}."),
        ("bruno@exemplo.com", "Cota extra lançada",
         f"Troca do portão: a parte da unidade 301 é R$ 900,00, em 3 parcelas mensais, "
         f"com o primeiro vencimento em {data}."),
    ]


def test_cota_extra_pela_fracao(cliente, cenario):
    fracao(cliente, cenario["sindico"], cenario["u204"], "25")
    fracao(cliente, cenario["sindico"], cenario["u301"], "75")
    r = lote(cliente, cenario["sindico"], tipo="extra", rateio="fracao",
             descricao="Fundo de obras", valor="1000.00", parcelas=2)
    assert r.status_code == 201, r.text
    extras = por_unidade(cliente, cenario["sindico"], origem="extra")
    assert sorted(c["valor"] for c in extras[cenario["u204"]]) == ["125.00", "125.00"]
    assert sorted(c["valor"] for c in extras[cenario["u301"]]) == ["375.00", "375.00"]


@pytest.mark.parametrize("extra", [
    {"parcelas": 3},                        # a taxa do mês não se parcela
    {"parcelas": 25, "tipo": "extra"},
    {"valor": "0"},
    {"rateio": "outro"},
    {"tipo": "multa"},
    {"vencimento": (hoje_local().replace(day=1) - timedelta(days=1)).isoformat()},
])
def test_dados_invalidos(cliente, cenario, extra):
    assert lote(cliente, cenario["sindico"], **extra).status_code == 422


def test_valor_pequeno_demais_para_ratear(cliente, cenario):
    fracao(cliente, cenario["sindico"], cenario["u204"], "50")
    fracao(cliente, cenario["sindico"], cenario["u301"], "50")
    r = lote(cliente, cenario["sindico"], rateio="fracao", valor="0.01")
    assert r.status_code == 400


def test_so_o_sindico(cliente, cenario):
    assert lote(cliente, cenario["ana"]).status_code == 403
    assert lote(cliente, cenario["porteiro"]).status_code == 403


@pytest.mark.parametrize("valor", ["0", "-1", "100.01", "12.34567"])
def test_fracao_ideal_invalida(cliente, cenario, valor):
    assert fracao(cliente, cenario["sindico"], cenario["u204"], valor).status_code == 422


def test_fracao_ideal_fica_no_historico_e_pode_ser_apagada(cliente, cenario):
    r = fracao(cliente, cenario["sindico"], cenario["u204"], "12.5")
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["fracao_ideal"]) == Decimal("12.5")
    assert r.json()["ultima_alteracao"]["descricao"] == "Alterou a fração ideal"
    r = fracao(cliente, cenario["sindico"], cenario["u204"], None)
    assert r.status_code == 200 and r.json()["fracao_ideal"] is None
    unidades = cliente.get("/api/v1/condominios/meu/unidades",
                           headers=cab(cenario["sindico"])).json()
    assert all("fracao_ideal" in u for u in unidades)
