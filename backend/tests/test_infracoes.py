"""Advertências e multas por infração do regimento.

Situação real: a festa vai até as 3h, o cachorro suja o hall, a obra
começa sem aviso. O síndico precisa notificar o apartamento — e o Código
Civil prevê multa para quem descumpre os deveres do condomínio (art.
1.336, § 2º: até 5 vezes a contribuição mensal; art. 1.337: o
reincidente) —, mas a multa aplicada sem dar chance de defesa costuma
ser anulada na Justiça. O sistema não tinha nada disso: o aviso ia por
bilhete embaixo da porta.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.routers import infracoes as rota
from app.core.tempo import hoje_local
from app.services import notificacao
from tests.fixtures import CPFS, cab, cadastrar_morador
from tests.test_financeiro import COMPETENCIA, cenario, gerar_cobranca  # noqa: F401

URL = "/api/v1/infracoes"


def notificar(cliente, tok, unidade_id, tipo="multa", valor=None, **extra):
    corpo = {"unidade_id": unidade_id, "tipo": tipo,
             "descricao": "Som alto depois das 22h, no salão do apartamento.",
             "artigo": "Regimento interno, art. 12",
             "ocorrida_em": (hoje_local() - timedelta(days=2)).isoformat(),
             "prazo_defesa_dias": 10}
    if valor is None and tipo == "multa":
        valor = "300.00"
    if valor is not None:
        corpo["valor"] = valor
    corpo.update(extra)
    return cliente.post(URL, json=corpo, headers=cab(tok))


def defender(cliente, tok, infracao_id, texto="Era aniversário e terminou às 22h30."):
    return cliente.post(f"{URL}/{infracao_id}/defesa", json={"texto": texto}, headers=cab(tok))


def decidir(cliente, tok, infracao_id, manter=True, motivo="A câmera do hall mostra som até 1h."):
    return cliente.post(f"{URL}/{infracao_id}/decisao", json={"manter": manter, "motivo": motivo},
                        headers=cab(tok))


@pytest.fixture
def com_taxa(cliente, cenario):
    """A multa é limitada pela contribuição mensal: o apartamento precisa
    ter a taxa lançada."""
    for u in ("u204", "u301"):
        assert gerar_cobranca(cliente, cenario["sindico"], cenario[u]).status_code == 201
    return cenario


def test_notificacao_defesa_e_multa_mantida(cliente, com_taxa, monkeypatch):
    c = com_taxa
    avisos = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: avisos.append(destino))
    r = notificar(cliente, c["sindico"], c["u204"])
    assert r.status_code == 201, r.text
    inf = r.json()
    assert inf["status"] == "notificada" and inf["unidade"] == "204"
    assert inf["prazo_defesa"] == (hoje_local() + timedelta(days=10)).isoformat()
    assert avisos == ["ana@exemplo.com"]
    # Só o apartamento notificado vê; a portaria não.
    assert len(cliente.get(URL, headers=cab(c["ana"])).json()) == 1
    assert cliente.get(URL, headers=cab(c["bruno"])).json() == []
    assert cliente.get(URL, headers=cab(c["porteiro"])).status_code == 403

    r = defender(cliente, c["ana"], inf["id"])
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "defesa_apresentada"
    assert avisos[-1] == "sindico@exemplo.com"
    assert defender(cliente, c["ana"], inf["id"]).status_code == 409

    r = decidir(cliente, c["sindico"], inf["id"])
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmada" and r.json()["cobranca_id"]
    assert avisos[-1] == "ana@exemplo.com"
    # A multa vira cobrança do apartamento, ao lado da taxa do mês.
    multas = [x for x in cliente.get("/api/v1/financeiro/cobrancas", headers=cab(c["ana"])).json()
              if x["origem"] == "multa"]
    assert len(multas) == 1 and multas[0]["valor"] == "300.00"
    assert decidir(cliente, c["sindico"], inf["id"]).status_code == 409


def test_defesa_acolhida_anula(cliente, com_taxa):
    c = com_taxa
    inf = notificar(cliente, c["sindico"], c["u204"]).json()
    defender(cliente, c["ana"], inf["id"])
    r = decidir(cliente, c["sindico"], inf["id"], manter=False, motivo="Era outro apartamento.")
    assert r.status_code == 200
    assert r.json()["status"] == "anulada" and r.json()["cobranca_id"] is None
    assert all(x["origem"] != "multa" for x in
               cliente.get("/api/v1/financeiro/cobrancas", headers=cab(c["ana"])).json())


def test_limite_de_cinco_vezes_a_taxa(cliente, com_taxa):
    c = com_taxa
    r = notificar(cliente, c["sindico"], c["u204"], valor="1600.01")
    assert r.status_code == 400 and "5 vezes" in r.json()["detalhe"]
    assert notificar(cliente, c["sindico"], c["u204"], valor="1600.00").status_code == 201


def test_multa_sem_taxa_lancada(cliente, cenario):
    r = notificar(cliente, cenario["sindico"], cenario["u204"])
    assert r.status_code == 409 and "taxa" in r.json()["detalhe"]
    # A advertência não tem valor: não depende da taxa.
    assert notificar(cliente, cenario["sindico"], cenario["u204"], tipo="advertencia").status_code == 201


def test_sem_defesa_so_depois_do_prazo(cliente, com_taxa, monkeypatch):
    c = com_taxa
    inf = notificar(cliente, c["sindico"], c["u204"]).json()
    r = decidir(cliente, c["sindico"], inf["id"])
    assert r.status_code == 409 and "prazo" in r.json()["detalhe"]
    depois = hoje_local() + timedelta(days=11)
    monkeypatch.setattr(rota, "_hoje", lambda: depois)
    r = defender(cliente, c["ana"], inf["id"])
    assert r.status_code == 409 and "prazo" in r.json()["detalhe"]
    assert decidir(cliente, c["sindico"], inf["id"]).json()["status"] == "confirmada"


def test_advertencia(cliente, cenario):
    r = notificar(cliente, cenario["sindico"], cenario["u204"], tipo="advertencia", valor="10.00")
    assert r.status_code == 422
    inf = notificar(cliente, cenario["sindico"], cenario["u204"], tipo="advertencia").json()
    defender(cliente, cenario["ana"], inf["id"])
    r = decidir(cliente, cenario["sindico"], inf["id"])
    assert r.json()["status"] == "confirmada" and r.json()["cobranca_id"] is None


def test_a_multa_nao_trava_a_taxa_do_mes(cliente, cenario):
    """Antes, uma cobrança por apartamento e mês: a multa do mês impediria
    lançar a taxa."""
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u301"]).status_code == 201
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"],
                          competencia=(hoje_local().replace(day=1) - timedelta(days=1))
                          .replace(day=1).isoformat()).status_code == 201
    inf = notificar(cliente, cenario["sindico"], cenario["u204"]).json()
    defender(cliente, cenario["ana"], inf["id"])
    assert decidir(cliente, cenario["sindico"], inf["id"]).status_code == 200
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 201
    # A taxa continua uma por mês.
    assert gerar_cobranca(cliente, cenario["sindico"], cenario["u204"]).status_code == 409


def test_reincidencia(cliente, com_taxa):
    c = com_taxa
    primeira = notificar(cliente, c["sindico"], c["u204"], tipo="advertencia").json()
    defender(cliente, c["ana"], primeira["id"])
    decidir(cliente, c["sindico"], primeira["id"])
    segunda = notificar(cliente, c["sindico"], c["u204"]).json()
    assert segunda["reincidencias"] == 1


@pytest.mark.parametrize("corpo", [
    {"descricao": "x"},
    {"prazo_defesa_dias": 2},
    {"prazo_defesa_dias": 60},
    {"ocorrida_em": (hoje_local() + timedelta(days=1)).isoformat()},
    {"valor": "-5.00"},
    {"tipo": "prisao"},
])
def test_dados_invalidos(cliente, com_taxa, corpo):
    assert notificar(cliente, com_taxa["sindico"], com_taxa["u204"], **corpo).status_code == 422


def test_quem_pode(cliente, com_taxa):
    c = com_taxa
    assert notificar(cliente, c["ana"], c["u301"]).status_code == 403
    assert notificar(cliente, c["porteiro"], c["u301"]).status_code == 403
    inf = notificar(cliente, c["sindico"], c["u204"]).json()
    assert defender(cliente, c["bruno"], inf["id"]).status_code == 404
    assert decidir(cliente, c["ana"], inf["id"]).status_code == 403
    assert notificar(cliente, c["sindico"], 999999).status_code == 404


def test_quem_chegou_depois_nao_ve(cliente, com_taxa):
    c = com_taxa
    notificar(cliente, c["sindico"], c["u204"])
    _, tok_carla = cadastrar_morador(cliente, c["sindico"], c["cond"], email="carla@exemplo.com",
                                     cpf=CPFS[4], unidade="204")
    assert cliente.get(URL, headers=cab(tok_carla)).json() == []
