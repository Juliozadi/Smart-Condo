"""Comunicado para um bloco ou para um apartamento.

Situação real: "falta de água no bloco B amanhã" não interessa ao bloco A;
a advertência por barulho é do apartamento 101 do bloco B, e só dele. O
comunicado ia sempre para o condomínio inteiro: o aviso do bloco virava
ruído para todos, e a advertência ficava à vista dos vizinhos — dado que
expõe o morador.
"""
from __future__ import annotations

import pytest

from app.services import notificacao
from tests.fixtures import (
    CPFS, cab, cadastrar_porteiro, criar_condominio_como_admin, criar_sindico, montar_condominio,
    token,
)

URL = "/api/v1/comunicados"


def morador_em(cliente, sindico, cond, email, cpf, bloco, numero):
    r = cliente.post("/api/v1/auth/cadastro/morador", json={
        "nome": "Morador Teste", "email": email, "cpf": cpf, "telefone": "(67) 99999-0002",
        "senha": "senhaforte123", "codigo_condominio": cond["codigo_acesso"],
        "unidade_numero": numero, "unidade_bloco": bloco, "tipo_ocupacao": "proprietario"})
    assert r.status_code == 201, r.text
    corpo = r.json()
    cliente.post("/api/v1/auth/confirmar", json={"email": email, "codigo": corpo["codigo_debug"]})
    ap = cliente.post(f"/api/v1/usuarios/{corpo['usuario']['id']}/aprovacao",
                      json={"aprovado": True}, headers=cab(sindico))
    assert ap.status_code == 200, ap.text
    return token(cliente, email, "senhaforte123")


@pytest.fixture
def predio(cliente, db):
    base = montar_condominio(cliente, db)
    s, cond = base["sindico"], base["cond"]
    a101 = morador_em(cliente, s, cond, "a101@exemplo.com", CPFS[1], "A", "101")
    b101 = morador_em(cliente, s, cond, "b101@exemplo.com", CPFS[3], "B", "101")
    b202 = morador_em(cliente, s, cond, "b202@exemplo.com", CPFS[4], "B", "202")
    _, porteiro = cadastrar_porteiro(cliente, s, cond, cpf=CPFS[2])
    unidades = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(s)).json()
    uid = {(u["bloco"], u["numero"]): u["id"] for u in unidades}
    return {**base, "a101": a101, "b101": b101, "b202": b202, "porteiro": porteiro,
            "u_b101": uid[("B", "101")]}


@pytest.fixture
def avisados(monkeypatch):
    lista = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: lista.append(destino))
    return lista


def publicar(cliente, tok, **extra):
    corpo = {"titulo": "Falta de água", "conteudo": "Amanhã, das 8h às 12h.", **extra}
    return cliente.post(URL, json=corpo, headers=cab(tok))


def titulos(cliente, tok):
    return [c["titulo"] for c in cliente.get(URL, headers=cab(tok)).json()]


def test_geral_continua_para_todos(cliente, predio, avisados):
    r = publicar(cliente, predio["sindico"])
    assert r.status_code == 201, r.text
    assert r.json()["destino"] == "Todo o condomínio"
    assert sorted(avisados) == ["a101@exemplo.com", "b101@exemplo.com", "b202@exemplo.com"]
    for quem in ("a101", "b101", "b202", "porteiro"):
        assert titulos(cliente, predio[quem]) == ["Falta de água"]


def test_aviso_para_um_bloco(cliente, predio, avisados):
    r = publicar(cliente, predio["sindico"], bloco="B")
    assert r.status_code == 201, r.text
    assert r.json()["destino"] == "Bloco B"
    assert sorted(avisados) == ["b101@exemplo.com", "b202@exemplo.com"]
    assert titulos(cliente, predio["b101"]) == ["Falta de água"]
    assert titulos(cliente, predio["b202"]) == ["Falta de água"]
    assert titulos(cliente, predio["a101"]) == []
    # A portaria precisa saber da falta de água no bloco.
    assert titulos(cliente, predio["porteiro"]) == ["Falta de água"]


def test_advertencia_so_para_o_apartamento(cliente, predio, avisados):
    r = publicar(cliente, predio["sindico"], unidade_id=predio["u_b101"],
                 titulo="Advertência: barulho", conteudo="Barulho após as 22h em 10/10.")
    assert r.status_code == 201, r.text
    assert r.json()["destino"] == "Apto B 101"
    assert avisados == ["b101@exemplo.com"]
    assert titulos(cliente, predio["b101"]) == ["Advertência: barulho"]
    # Nem o vizinho de bloco, nem a portaria, veem a advertência.
    assert titulos(cliente, predio["b202"]) == []
    assert titulos(cliente, predio["porteiro"]) == []
    assert titulos(cliente, predio["sindico"]) == ["Advertência: barulho"]


def test_quem_chega_depois_nao_ve_a_advertencia_do_anterior(cliente, predio):
    publicar(cliente, predio["sindico"], unidade_id=predio["u_b101"],
             titulo="Advertência: barulho", conteudo="Barulho após as 22h em 10/10.")
    novo = morador_em(cliente, predio["sindico"], predio["cond"], "novo@exemplo.com", CPFS[5],
                      "B", "101")
    assert titulos(cliente, novo) == []
    assert titulos(cliente, predio["b101"]) == ["Advertência: barulho"]


def test_nao_marca_como_lido_o_que_nao_e_para_ele(cliente, predio):
    c = publicar(cliente, predio["sindico"], unidade_id=predio["u_b101"]).json()
    r = cliente.post(f"{URL}/{c['id']}/leitura", headers=cab(predio["b202"]))
    assert r.status_code == 404
    assert cliente.post(f"{URL}/{c['id']}/leitura",
                        headers=cab(predio["b101"])).status_code == 200


@pytest.mark.parametrize("destino", [
    {"bloco": "Z"},
    {"bloco": "B", "unidade_id": "u_b101"},
    {"unidade_id": 999999},
])
def test_destino_invalido(cliente, predio, destino):
    if destino.get("unidade_id") == "u_b101":
        destino = {**destino, "unidade_id": predio["u_b101"]}
    r = publicar(cliente, predio["sindico"], **destino)
    assert r.status_code in (404, 422), (destino, r.text)


def test_unidade_de_outro_condominio(cliente, predio):
    outro = criar_condominio_como_admin(cliente, predio["admin"], nome="Aurora",
                                        cnpj="45.997.418/0001-53")
    _, sindico2 = criar_sindico(cliente, predio["admin"], outro["id"], email="s2@exemplo.com",
                                cpf="529.982.247-25")
    r = publicar(cliente, sindico2, unidade_id=predio["u_b101"])
    assert r.status_code == 404
