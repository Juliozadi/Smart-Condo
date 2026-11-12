"""Visões, funções e gatilhos do banco, usados pelo sistema.

A suíte inteira roda com os gatilhos ligados (conftest); aqui ficam o que
eles fazem e a tela do síndico que lê o que o próprio banco calcula.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.tempo import hoje_local
from tests.fixtures import cab, montar_condominio
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/banco"
ROTAS = ["/situacao-unidades", "/balancete", "/log-cobrancas", "/rateio?total=100.00"]


def _cobranca(cliente, tok, unidade_id, dias=10, valor="300.00"):
    hoje = hoje_local()
    r = cliente.post("/api/v1/financeiro/cobrancas", headers=cab(tok), json={
        "unidade_id": unidade_id, "competencia": hoje.replace(day=1).isoformat(),
        "descricao": "Taxa de condomínio", "valor": valor,
        "vencimento": (hoje + timedelta(days=dias)).isoformat()})
    assert r.status_code == 201, r.text
    return r.json()


def _fracao(cliente, tok, unidade_id, valor):
    r = cliente.put(f"/api/v1/condominios/meu/unidades/{unidade_id}",
                    json={"fracao_ideal": valor}, headers=cab(tok))
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("rota", ROTAS)
def test_so_o_sindico(cliente, cenario, rota):
    assert cliente.get(URL + rota, headers=cab(cenario["ana"])).status_code == 403
    assert cliente.get(URL + rota, headers=cab(cenario["porteiro"])).status_code == 403
    assert cliente.get(URL + rota).status_code == 401
    # O rateio responde 409 enquanto faltam as frações: o síndico passa.
    assert cliente.get(URL + rota, headers=cab(cenario["sindico"])).status_code in (200, 409)


def test_pagamento_pela_api_aciona_os_gatilhos(cliente, cenario):
    c = _cobranca(cliente, cenario["sindico"], cenario["u204"])
    assert cliente.get(f"{URL}/log-cobrancas", headers=cab(cenario["sindico"])).json() == []
    r = cliente.post(f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
                     headers=cab(cenario["ana"]), json={"valor": "300.00", "forma": "pix"})
    assert r.status_code == 201, r.text
    log = cliente.get(f"{URL}/log-cobrancas", headers=cab(cenario["sindico"])).json()
    assert len(log) == 1
    assert log[0]["cobranca_id"] == c["id"] and log[0]["apartamento"] == "204"
    assert (log[0]["status_anterior"], log[0]["status_novo"]) == ("ABERTA", "PAGA")
    # A API continua dizendo o mesmo: paga.
    lista = cliente.get("/api/v1/financeiro/cobrancas", headers=cab(cenario["sindico"])).json()
    assert next(x for x in lista if x["id"] == c["id"])["status"] == "paga"


def test_correcao_de_valor_fica_no_log(cliente, cenario):
    c = _cobranca(cliente, cenario["sindico"], cenario["u204"])
    r = cliente.put(f"/api/v1/financeiro/cobrancas/{c['id']}", headers=cab(cenario["sindico"]),
                      json={"valor": "320.00"})
    assert r.status_code == 200, r.text
    log = cliente.get(f"{URL}/log-cobrancas", headers=cab(cenario["sindico"])).json()
    assert (log[0]["valor_anterior"], log[0]["valor_novo"]) == ("300.00", "320.00")


def test_situacao_e_balancete_vem_das_visoes(cliente, cenario):
    _cobranca(cliente, cenario["sindico"], cenario["u204"], dias=-5)
    c = _cobranca(cliente, cenario["sindico"], cenario["u301"])
    cliente.post(f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
                 headers=cab(cenario["bruno"]), json={"valor": "300.00", "forma": "pix"})
    situacao = {s["apartamento"]: s for s in
                cliente.get(f"{URL}/situacao-unidades", headers=cab(cenario["sindico"])).json()}
    assert situacao["204"]["situacao"] == "INADIMPLENTE"
    assert Decimal(situacao["204"]["valor_em_atraso"]) == Decimal("300.00")
    assert situacao["301"]["situacao"] == "EM DIA"
    balancete = cliente.get(f"{URL}/balancete", headers=cab(cenario["sindico"])).json()
    assert len(balancete) == 1 and Decimal(balancete[0]["receitas"]) == Decimal("300.00")


def test_rateio_pela_funcao_do_banco(cliente, cenario):
    r = cliente.get(f"{URL}/rateio?total=1000.01", headers=cab(cenario["sindico"]))
    assert r.status_code == 409 and "Faltam" in r.json()["detalhe"]
    _fracao(cliente, cenario["sindico"], cenario["u204"], "40")
    _fracao(cliente, cenario["sindico"], cenario["u301"], "50")
    r = cliente.get(f"{URL}/rateio?total=1000.01", headers=cab(cenario["sindico"]))
    assert r.status_code == 409
    assert r.json()["detalhe"] == "As frações ideais somam 90%; precisam somar 100%."
    _fracao(cliente, cenario["sindico"], cenario["u301"], "60")
    r = cliente.get(f"{URL}/rateio?total=1000.01", headers=cab(cenario["sindico"]))
    assert r.status_code == 200, r.text
    assert {p["apartamento"]: p["valor"] for p in r.json()} == {"204": "400.00", "301": "600.01"}


@pytest.mark.parametrize("total", ["0", "-5", "abc", "10000000.01", "1.001"])
def test_rateio_valor_invalido(cliente, cenario, total):
    r = cliente.get(f"{URL}/rateio?total={total}", headers=cab(cenario["sindico"]))
    assert r.status_code == 422


def test_outro_condominio_nao_ve(cliente, db, cenario):
    c = _cobranca(cliente, cenario["sindico"], cenario["u204"])
    cliente.post(f"/api/v1/financeiro/cobrancas/{c['id']}/pagamentos",
                 headers=cab(cenario["ana"]), json={"valor": "300.00", "forma": "pix"})
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert cliente.get(f"{URL}/log-cobrancas", headers=cab(s2)).json() == []
    assert cliente.get(f"{URL}/balancete", headers=cab(s2)).json() == []
    apartamentos = {s["apartamento"] for s in
                    cliente.get(f"{URL}/situacao-unidades", headers=cab(s2)).json()}
    assert "204" not in apartamentos


def test_gatilho_barra_pagamento_gravado_direto_no_banco(cliente, db, cenario):
    """Mesmo quem passar por fora da API não paga duas vezes nem paga o cancelado."""
    c = _cobranca(cliente, cenario["sindico"], cenario["u204"])
    sql = text("INSERT INTO pagamentos (cobranca_id, valor, encargos, forma, pago_em) "
               "VALUES (:c, :v, 0, 'PIX', now())")
    db.execute(sql, {"c": c["id"], "v": Decimal("300.00")})
    db.commit()
    with pytest.raises(DBAPIError, match="só falta 0.00"):
        db.execute(sql, {"c": c["id"], "v": Decimal("1.00")})
    db.rollback()
    outra = _cobranca(cliente, cenario["sindico"], cenario["u301"])
    cliente.post(f"/api/v1/financeiro/cobrancas/{outra['id']}/cancelamento",
                 headers=cab(cenario["sindico"]), json={"motivo": "Lançada por engano"})
    with pytest.raises(DBAPIError, match="cancelada: não recebe pagamento"):
        db.execute(sql, {"c": outra["id"], "v": Decimal("10.00")})
    db.rollback()
