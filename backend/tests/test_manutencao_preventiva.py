"""Manutenção preventiva e obrigações com vencimento.

Situação real: o AVCB vence e o seguro não cobre o incêndio; a recarga
dos extintores passa do prazo e a fiscalização multa; a caixa d'água
fica um ano sem limpeza. O síndico controlava numa planilha — ou na
memória. Agora cada obrigação tem a periodicidade e o próximo
vencimento, o painel avisa o que venceu ou está para vencer, e o
registro da realização renova o prazo (e pode lançar a despesa).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.api.routers import preventiva as rota
from app.core.tempo import hoje_local
from tests.fixtures import cab, montar_condominio
from tests.test_financeiro import cenario  # noqa: F401

URL = "/api/v1/manutencao-preventiva"
HOJE = hoje_local()


def criar(cliente, tok, **extra):
    corpo = {"nome": "Recarga dos extintores", "periodicidade_meses": 12,
             "proximo_vencimento": (HOJE + timedelta(days=90)).isoformat(),
             "antecedencia_aviso_dias": 30, "fornecedor": "Extintores Brasil"}
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def realizar(cliente, tok, plano_id, **extra):
    corpo = {"data": HOJE.isoformat()}
    corpo.update(extra)
    return cliente.post(f"{URL}/{plano_id}/realizacoes", json=corpo, headers=cab(tok))


def test_somar_meses_respeita_o_fim_do_mes():
    assert rota.somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert rota.somar_meses(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert rota.somar_meses(date(2026, 8, 15), 6) == date(2027, 2, 15)
    assert rota.somar_meses(date(2026, 12, 10), 12) == date(2027, 12, 10)


def test_situacao_conforme_o_vencimento(cliente, cenario):
    s = cenario["sindico"]
    assert criar(cliente, s, nome="AVCB", periodicidade_meses=60,
                 proximo_vencimento=(HOJE + timedelta(days=90)).isoformat()).status_code == 201
    assert criar(cliente, s, nome="Limpeza da caixa d'água", periodicidade_meses=6,
                 proximo_vencimento=(HOJE + timedelta(days=10)).isoformat()).status_code == 201
    r = criar(cliente, s, proximo_vencimento=(HOJE - timedelta(days=1)).isoformat())
    assert r.status_code == 201, r.text

    lista = cliente.get(URL, headers=cab(s)).json()
    # O que venceu primeiro, em cima.
    assert [p["nome"] for p in lista] == ["Recarga dos extintores", "Limpeza da caixa d'água", "AVCB"]
    assert [p["situacao"] for p in lista] == ["vencida", "vence_em_breve", "em_dia"]
    assert [p["dias_para_vencer"] for p in lista] == [-1, 10, 90]


def test_realizacao_renova_o_prazo(cliente, cenario):
    s = cenario["sindico"]
    plano = criar(cliente, s, proximo_vencimento=(HOJE - timedelta(days=5)).isoformat()).json()
    r = realizar(cliente, s, plano["id"], observacao="Recarregados os 14 extintores.")
    assert r.status_code == 201, r.text
    p = cliente.get(URL, headers=cab(s)).json()[0]
    assert p["ultima_realizacao"] == HOJE.isoformat()
    assert p["proximo_vencimento"] == rota.somar_meses(HOJE, 12).isoformat()
    assert p["situacao"] == "em_dia"

    historico = cliente.get(f"{URL}/{plano['id']}/realizacoes", headers=cab(s)).json()
    assert len(historico) == 1 and historico[0]["registrada_por_nome"] == "Roberto Nascimento"
    assert historico[0]["observacao"] == "Recarregados os 14 extintores."


def test_realizacao_antiga_nao_recua_o_prazo(cliente, cenario):
    s = cenario["sindico"]
    plano = criar(cliente, s).json()
    recente = HOJE - timedelta(days=30)
    assert realizar(cliente, s, plano["id"], data=recente.isoformat()).status_code == 201
    # Lançar depois uma realização antiga (esquecida) não volta o vencimento.
    antiga = HOJE - timedelta(days=400)
    assert realizar(cliente, s, plano["id"], data=antiga.isoformat()).status_code == 201
    p = cliente.get(URL, headers=cab(s)).json()[0]
    assert p["ultima_realizacao"] == recente.isoformat()
    assert p["proximo_vencimento"] == rota.somar_meses(recente, 12).isoformat()
    historico = cliente.get(f"{URL}/{plano['id']}/realizacoes", headers=cab(s)).json()
    assert [h["data"] for h in historico] == [recente.isoformat(), antiga.isoformat()]


def test_custo_lanca_a_despesa(cliente, cenario):
    s = cenario["sindico"]
    plano = criar(cliente, s).json()
    r = realizar(cliente, s, plano["id"], custo="380.00", lancar_despesa=True)
    assert r.status_code == 201, r.text
    assert r.json()["despesa_id"]
    despesas = cliente.get("/api/v1/financeiro/despesas", headers=cab(s)).json()
    assert len(despesas) == 1
    d = despesas[0]
    assert d["categoria"] == "manutencao" and d["valor"] == "380.00"
    assert "Recarga dos extintores" in d["descricao"] and d["fornecedor"] == "Extintores Brasil"
    assert d["data"] == HOJE.isoformat()

    # Sem pedir, o custo fica só no histórico.
    r = realizar(cliente, s, plano["id"], custo="120.00")
    assert r.status_code == 201 and r.json()["despesa_id"] is None
    assert len(cliente.get("/api/v1/financeiro/despesas", headers=cab(s)).json()) == 1


def test_despesa_sem_custo_nao_da(cliente, cenario):
    plano = criar(cliente, cenario["sindico"]).json()
    r = realizar(cliente, cenario["sindico"], plano["id"], lancar_despesa=True)
    assert r.status_code == 422


@pytest.mark.parametrize("dias", [1, -(366 * 10 + 5)])
def test_data_da_realizacao_fora_do_razoavel(cliente, cenario, dias):
    plano = criar(cliente, cenario["sindico"]).json()
    r = realizar(cliente, cenario["sindico"], plano["id"],
                 data=(HOJE + timedelta(days=dias)).isoformat())
    assert r.status_code == 422


@pytest.mark.parametrize("campo,valor", [
    ("nome", ""), ("nome", "x" * 121), ("periodicidade_meses", 0),
    ("periodicidade_meses", 121), ("antecedencia_aviso_dias", -1),
    ("antecedencia_aviso_dias", 181), ("custo_invalido", None),
])
def test_plano_invalido(cliente, cenario, campo, valor):
    if campo == "custo_invalido":
        plano = criar(cliente, cenario["sindico"]).json()
        r = realizar(cliente, cenario["sindico"], plano["id"], custo="-5.00")
    else:
        r = criar(cliente, cenario["sindico"], **{campo: valor})
    assert r.status_code == 422


def test_nome_repetido_no_mesmo_condominio(cliente, cenario):
    s = cenario["sindico"]
    assert criar(cliente, s).status_code == 201
    r = criar(cliente, s, nome="recarga dos EXTINTORES")
    assert r.status_code == 409


def test_editar_e_remover(cliente, cenario):
    s = cenario["sindico"]
    plano = criar(cliente, s).json()
    novo = (HOJE + timedelta(days=200)).isoformat()
    r = cliente.put(f"{URL}/{plano['id']}", headers=cab(s),
                    json={"nome": "Recarga e teste dos extintores", "periodicidade_meses": 6,
                          "proximo_vencimento": novo, "antecedencia_aviso_dias": 45,
                          "fornecedor": None, "observacao": "Teste hidrostático a cada 5 anos."})
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["nome"] == "Recarga e teste dos extintores" and p["periodicidade_meses"] == 6
    assert p["fornecedor"] is None and p["proximo_vencimento"] == novo

    assert cliente.delete(f"{URL}/{plano['id']}", headers=cab(s)).status_code == 200
    assert cliente.get(URL, headers=cab(s)).json() == []
    assert realizar(cliente, s, plano["id"]).status_code == 404
    # Removido, o nome fica livre para um plano novo.
    assert criar(cliente, s, nome="Recarga e teste dos extintores").status_code == 201


def test_so_o_sindico(cliente, cenario):
    plano = criar(cliente, cenario["sindico"]).json()
    for quem in ("ana", "porteiro"):
        tok = cenario[quem]
        assert cliente.get(URL, headers=cab(tok)).status_code == 403
        assert criar(cliente, tok).status_code == 403
        assert realizar(cliente, tok, plano["id"]).status_code == 403


def test_outro_condominio_nao_alcanca(cliente, db, cenario):
    plano = criar(cliente, cenario["sindico"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    s2 = outro["sindico"]
    assert cliente.get(URL, headers=cab(s2)).json() == []
    assert realizar(cliente, s2, plano["id"]).status_code == 404
    assert cliente.get(f"{URL}/{plano['id']}/realizacoes", headers=cab(s2)).status_code == 404
    assert cliente.put(f"{URL}/{plano['id']}", headers=cab(s2),
                       json={"nome": "Invadido"}).status_code == 404
    assert cliente.delete(f"{URL}/{plano['id']}", headers=cab(s2)).status_code == 404
