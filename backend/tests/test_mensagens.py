"""Testes do chat (seção 13.5.2).

O que estes testes protegem: a conversa só acontece entre pessoas ativas
do mesmo condomínio e dentro das duplas permitidas; ninguém descobre, pela
resposta, quem existe em outro condomínio; e o contador de não lidas zera
quando a conversa é aberta.
"""
from __future__ import annotations

import pytest

from tests.fixtures import CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio


@pytest.fixture
def cen(cliente, db):
    c = montar_condominio(cliente, db)
    c["porteiro_id"], c["porteiro"] = cadastrar_porteiro(cliente, c["sindico"], c["cond"])
    c["morador_id"], c["morador"] = cadastrar_morador(cliente, c["sindico"], c["cond"])
    c["morador2_id"], c["morador2"] = cadastrar_morador(
        cliente, c["sindico"], c["cond"], email="vizinho@exemplo.com", cpf=CPFS[3], unidade="301")
    return c


def enviar(cliente, tok, para, texto):
    return cliente.post(f"/api/v1/mensagens/com/{para}", json={"texto": texto}, headers=cab(tok))


def test_sindico_e_porteiro_conversam_e_nao_lidas_zeram(cliente, cen):
    r = enviar(cliente, cen["sindico"], cen["porteiro_id"], "  Bom dia, tudo certo na portaria?  ")
    assert r.status_code == 201, r.text
    assert r.json()["texto"] == "Bom dia, tudo certo na portaria?"
    assert r.json()["minha"] is True

    nao = cliente.get("/api/v1/mensagens/nao-lidas", headers=cab(cen["porteiro"])).json()
    assert nao["total"] == 1

    conversa = cliente.get(f"/api/v1/mensagens/com/{cen['sindico_id']}", headers=cab(cen["porteiro"]))
    assert conversa.status_code == 200
    assert [m["texto"] for m in conversa.json()] == ["Bom dia, tudo certo na portaria?"]
    assert conversa.json()[0]["minha"] is False

    assert cliente.get("/api/v1/mensagens/nao-lidas", headers=cab(cen["porteiro"])).json()["total"] == 0


def test_depois_de_traz_so_as_novas(cliente, cen):
    primeira = enviar(cliente, cen["morador"], cen["porteiro_id"], "Chegou encomenda?").json()
    enviar(cliente, cen["porteiro"], cen["morador_id"], "Chegou sim, está na portaria.")
    novas = cliente.get(f"/api/v1/mensagens/com/{cen['porteiro_id']}?depois_de={primeira['id']}",
                        headers=cab(cen["morador"])).json()
    assert [m["texto"] for m in novas] == ["Chegou sim, está na portaria."]


def test_morador_nao_conversa_com_outro_morador(cliente, cen):
    """O sistema não entrega o contato de um vizinho a outro morador."""
    assert enviar(cliente, cen["morador"], cen["morador2_id"], "oi vizinho").status_code == 404
    assert cliente.get(f"/api/v1/mensagens/com/{cen['morador2_id']}",
                       headers=cab(cen["morador"])).status_code == 404
    ids = [c["id"] for c in cliente.get("/api/v1/mensagens/contatos", headers=cab(cen["morador"])).json()]
    assert cen["morador2_id"] not in ids
    assert set(ids) == {cen["sindico_id"], cen["porteiro_id"]}


def test_outro_condominio_nao_existe_para_o_chat(cliente, db, cen):
    outro = montar_condominio(cliente, db, nome="Edifício Aurora", cnpj="04.252.011/0001-10",
                              email_sindico="sindico2@exemplo.com", cpf_sindico=CPFS[4],
                              email_admin="admin2@exemplo.com", cpf_admin=CPFS[5])
    r = enviar(cliente, cen["sindico"], outro["sindico_id"], "olá")
    # A mesma resposta de um id que não existe: não revela que ele existe.
    assert r.status_code == 404
    assert enviar(cliente, cen["sindico"], 999999, "olá").json() == r.json()


def test_administrador_nao_participa(cliente, cen):
    r = cliente.get("/api/v1/mensagens/contatos", headers=cab(cen["admin"]))
    assert r.status_code == 403


@pytest.mark.parametrize("texto", ["", "   ", "x" * 2001])
def test_recusa_mensagem_vazia_ou_longa(cliente, cen, texto):
    assert enviar(cliente, cen["sindico"], cen["porteiro_id"], texto).status_code == 422


def test_contatos_trazem_telefone_e_resumo(cliente, cen):
    enviar(cliente, cen["porteiro"], cen["sindico_id"], "Portão da garagem travou.")
    contatos = cliente.get("/api/v1/mensagens/contatos", headers=cab(cen["sindico"])).json()
    # Quem mandou mensagem por último vem primeiro.
    assert contatos[0]["id"] == cen["porteiro_id"]
    assert contatos[0]["nao_lidas"] == 1
    assert contatos[0]["ultima_mensagem"] == "Portão da garagem travou."
    assert contatos[0]["telefone"]
    assert {c["papel"] for c in contatos} == {"porteiro", "morador"}


def test_nao_manda_mensagem_para_si_mesmo(cliente, cen):
    assert enviar(cliente, cen["sindico"], cen["sindico_id"], "eu").status_code == 404


def test_exige_sessao(cliente):
    assert cliente.get("/api/v1/mensagens/contatos").status_code == 401
