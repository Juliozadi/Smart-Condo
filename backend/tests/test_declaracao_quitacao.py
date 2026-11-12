"""Declaração de quitação condominial.

Situação real: o dono vende o apartamento, e o comprador (e o cartório,
na escritura — Lei 7.433/1985, art. 2º, § 2º) quer a prova de que não
há taxa de condomínio atrasada, porque a dívida acompanha o imóvel
(Código Civil, art. 1.345). Isso era um papel assinado pelo síndico,
que ninguém conseguia conferir. Agora o apartamento em dia emite a
declaração, e qualquer um confere pelo código — sem ver nome nem CPF.
"""
from __future__ import annotations

import re
from datetime import timedelta

import pytest

from app.api.routers import declaracoes as rota
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import cab, montar_condominio
from tests.test_financeiro import cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/declaracoes-quitacao"
HOJE = hoje_local()


def emitir(cliente, tok, unidade_id=None):
    corpo = {} if unidade_id is None else {"unidade_id": unidade_id}
    return cliente.post(URL, json=corpo, headers=cab(tok))


def verificar(cliente, codigo):
    return cliente.get(f"{URL}/verificar/{codigo}")


def pagar(cliente, tok, cobranca, valor=None):
    return cliente.post(f"/api/v1/financeiro/cobrancas/{cobranca['id']}/pagamentos",
                        json={"valor": valor or cobranca["valor"], "forma": "pix"},
                        headers=cab(tok))


@pytest.fixture
def depois_do_vencimento(monkeypatch):
    """A taxa de teste vence daqui a 7 dias; a declaração olha 10 dias à
    frente, quando ela já venceu."""
    monkeypatch.setattr(rota, "_hoje", lambda: HOJE + timedelta(days=10))


def test_apartamento_em_dia_emite_e_qualquer_um_confere(cliente, cenario):
    c = cenario
    # Uma taxa que ainda não venceu não é débito.
    assert gerar_cobranca(cliente, c["sindico"], c["u204"]).status_code == 201
    r = emitir(cliente, c["ana"])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["unidade"] == "204" and d["situacao"] == "valida"
    assert d["referencia_ate"] == HOJE.isoformat()
    assert d["valida_ate"] == (HOJE + timedelta(days=rota.VALIDADE_DIAS)).isoformat()
    assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}", d["codigo"])

    # Sem login: quem recebeu o código confere.
    r = verificar(cliente, d["codigo"])
    assert r.status_code == 200, r.text
    publica = r.json()
    assert publica["situacao"] == "valida" and publica["unidade"] == "204"
    assert publica["condominio_nome"] == c["cond"]["nome"]
    assert publica["condominio_cnpj"] == c["cond"]["cnpj"]
    assert publica["referencia_ate"] == HOJE.isoformat()
    # Nada de quem pediu: nem nome, nem e-mail, nem o id interno.
    assert "ana" not in r.text.lower() and "id" not in publica
    # O código vale digitado sem traços e em minúsculas.
    assert verificar(cliente, d["codigo"].replace("-", "").lower()).status_code == 200


def test_debito_vencido_impede_e_o_pagamento_libera(cliente, cenario, depois_do_vencimento):
    c = cenario
    cobranca = gerar_cobranca(cliente, c["sindico"], c["u204"]).json()
    r = emitir(cliente, c["ana"])
    assert r.status_code == 409
    assert "1 cobrança vencida" in r.json()["detalhe"] and "320,00" in r.json()["detalhe"]

    # Pagar uma parte não quita.
    assert pagar(cliente, c["ana"], cobranca, "100.00").status_code == 201
    assert emitir(cliente, c["ana"]).status_code == 409

    assert pagar(cliente, c["ana"], cobranca, "220.00").status_code == 201
    r = emitir(cliente, c["ana"])
    assert r.status_code == 201, r.text
    # A declaração é do dia em que foi pedida.
    assert r.json()["referencia_ate"] == (HOJE + timedelta(days=10)).isoformat()


def test_cobranca_cancelada_nao_e_debito(cliente, cenario, depois_do_vencimento):
    c = cenario
    cobranca = gerar_cobranca(cliente, c["sindico"], c["u204"]).json()
    r = cliente.post(f"/api/v1/financeiro/cobrancas/{cobranca['id']}/cancelamento",
                     json={"motivo": "Lançada em duplicidade"}, headers=cab(c["sindico"]))
    assert r.status_code == 200, r.text
    assert emitir(cliente, c["ana"]).status_code == 201


def test_debito_de_outro_apartamento_nao_conta(cliente, cenario, depois_do_vencimento):
    c = cenario
    gerar_cobranca(cliente, c["sindico"], c["u301"])
    assert emitir(cliente, c["ana"]).status_code == 201
    assert emitir(cliente, c["bruno"]).status_code == 409


def test_no_mesmo_dia_devolve_a_mesma(cliente, cenario):
    c = cenario
    primeira = emitir(cliente, c["ana"])
    segunda = emitir(cliente, c["ana"])
    assert primeira.status_code == 201 and segunda.status_code == 200
    assert primeira.json()["codigo"] == segunda.json()["codigo"]
    assert len(cliente.get(URL, headers=cab(c["ana"])).json()) == 1


def test_morador_so_do_proprio_apartamento(cliente, cenario):
    c = cenario
    d = emitir(cliente, c["ana"]).json()
    r = emitir(cliente, c["bruno"], c["u204"])
    assert r.status_code == 403
    assert cliente.get(URL, headers=cab(c["bruno"])).json() == []
    assert [x["codigo"] for x in cliente.get(URL, headers=cab(c["ana"])).json()] == [d["codigo"]]
    # O morador não revoga.
    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": "Quero cancelar"},
                     headers=cab(c["ana"]))
    assert r.status_code == 403


def test_sindico_emite_e_revoga_com_motivo(cliente, cenario, monkeypatch):
    c = cenario
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append((destino, mensagem)))
    assert emitir(cliente, c["sindico"]).status_code == 422
    r = emitir(cliente, c["sindico"], c["u301"])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["unidade"] == "301" and d["pode_revogar"] is True

    motivo = "O pagamento de setembro foi estornado pelo banco."
    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": motivo},
                     headers=cab(c["sindico"]))
    assert r.status_code == 200, r.text
    assert r.json()["situacao"] == "revogada" and r.json()["motivo_revogacao"] == motivo
    assert [destino for destino, _ in avisos] == ["bruno@exemplo.com"]
    assert motivo in avisos[0][1]

    publica = verificar(cliente, d["codigo"]).json()
    assert publica["situacao"] == "revogada" and publica["revogada_em"]
    # O motivo fica entre o condomínio e o apartamento.
    assert "estornado" not in str(publica)

    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": motivo},
                     headers=cab(c["sindico"]))
    assert r.status_code == 409
    # Revogada a de hoje, pedir de novo gera outra, com outro código.
    nova = emitir(cliente, c["bruno"])
    assert nova.status_code == 201 and nova.json()["codigo"] != d["codigo"]


@pytest.mark.parametrize("motivo", ["", "ok", "x" * 501])
def test_revogacao_pede_motivo(cliente, cenario, motivo):
    d = emitir(cliente, cenario["ana"]).json()
    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": motivo},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 422


def test_passado_o_prazo_a_declaracao_vence(cliente, cenario, monkeypatch):
    d = emitir(cliente, cenario["ana"]).json()
    monkeypatch.setattr(rota, "_hoje", lambda: HOJE + timedelta(days=rota.VALIDADE_DIAS + 1))
    assert verificar(cliente, d["codigo"]).json()["situacao"] == "vencida"
    assert cliente.get(URL, headers=cab(cenario["ana"])).json()[0]["situacao"] == "vencida"


def test_vencida_nao_se_revoga(cliente, cenario, monkeypatch):
    d = emitir(cliente, cenario["ana"]).json()
    monkeypatch.setattr(rota, "_hoje", lambda: HOJE + timedelta(days=rota.VALIDADE_DIAS + 1))
    lista = cliente.get(URL, headers=cab(cenario["sindico"])).json()
    assert lista[0]["situacao"] == "vencida" and lista[0]["pode_revogar"] is False
    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": "Pagamento estornado"},
                     headers=cab(cenario["sindico"]))
    assert r.status_code == 409 and "venceu" in r.json()["detalhe"]


def test_portaria_nao_emite_nem_lista(cliente, cenario):
    assert emitir(cliente, cenario["porteiro"], cenario["u204"]).status_code == 403
    assert cliente.get(URL, headers=cab(cenario["porteiro"])).status_code == 403


def test_outro_condominio_nao_alcanca(cliente, db, cenario):
    c = cenario
    d = emitir(cliente, c["ana"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    assert emitir(cliente, outro["sindico"], c["u204"]).status_code == 404
    assert cliente.get(URL, headers=cab(outro["sindico"])).json() == []
    r = cliente.post(f"{URL}/{d['id']}/revogacao", json={"motivo": "Tentativa indevida"},
                     headers=cab(outro["sindico"]))
    assert r.status_code == 404


@pytest.mark.parametrize("codigo", ["AAAA", "AAAA-BBBB-CCCC-DDDD", "x" * 200, "'; DROP TABLE x"])
def test_codigo_que_nao_existe(cliente, cenario, codigo):
    assert verificar(cliente, codigo).status_code == 404


def test_adivinhar_codigos_e_barrado(cliente, cenario):
    respostas = [verificar(cliente, f"AAAA-BBBB-CCCC-{i:04d}").status_code for i in range(35)]
    assert respostas[:30] == [404] * 30 and set(respostas[30:]) == {429}
