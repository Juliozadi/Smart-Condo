"""Livro da portaria: a passagem de turno.

Situação real: o porteiro da noite sai às 7h e precisa avisar o da manhã
que o entregador volta às 10h para o 204, que o portão da garagem está
travando, que a moradora do 410 pediu para não interfonar depois das 22h.
Isso ia num caderno no balcão — que some, molha e ninguém sabe se foi
lido. O livro do sistema é o caderno: não se apaga nem se edita, e cada
anotação importante mostra quem já leu.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.routers import livro
from tests.fixtures import CPFS, cab, cadastrar_porteiro, montar_condominio
from tests.test_portaria import cenario  # noqa: F401

URL = "/api/v1/livro-portaria"


@pytest.fixture
def dois_porteiros(cliente, cenario):
    _, tok = cadastrar_porteiro(cliente, cenario["sindico"], cenario["cond"],
                                email="porteiro2@exemplo.com", cpf=CPFS[5])
    return {**cenario, "porteiro2": tok}


def anotar(cliente, tok, texto="Entregador volta às 10h para o 204.", importante=True):
    return cliente.post(URL, json={"texto": texto, "importante": importante}, headers=cab(tok))


def test_passagem_de_turno(cliente, dois_porteiros):
    c = dois_porteiros
    r = anotar(cliente, c["porteiro"])
    assert r.status_code == 201, r.text
    nota = r.json()
    assert nota["autor_nome"] and nota["importante"] is True
    # Quem escreveu não precisa dar ciência da própria anotação.
    assert nota["preciso_ler"] is False

    lista = cliente.get(URL, headers=cab(c["porteiro2"])).json()
    assert [n["id"] for n in lista] == [nota["id"]] and lista[0]["preciso_ler"] is True
    assert cliente.get(f"{URL}/pendentes", headers=cab(c["porteiro2"])).json()["total"] == 1

    r = cliente.post(f"{URL}/{nota['id']}/ciencia", headers=cab(c["porteiro2"]))
    assert r.status_code == 200, r.text
    assert r.json()["preciso_ler"] is False and len(r.json()["cientes"]) == 1
    assert cliente.get(f"{URL}/pendentes", headers=cab(c["porteiro2"])).json()["total"] == 0
    # Dar ciência de novo não duplica.
    assert len(cliente.post(f"{URL}/{nota['id']}/ciencia",
                            headers=cab(c["porteiro2"])).json()["cientes"]) == 1


def test_anotacao_comum_nao_pede_ciencia(cliente, dois_porteiros):
    c = dois_porteiros
    anotar(cliente, c["porteiro"], "Turno tranquilo, sem ocorrências.", importante=False)
    assert cliente.get(f"{URL}/pendentes", headers=cab(c["porteiro2"])).json()["total"] == 0


def test_o_livro_nao_se_apaga_nem_se_edita(cliente, dois_porteiros):
    c = dois_porteiros
    nota = anotar(cliente, c["porteiro"]).json()
    # Não há rota para apagar nem para editar.
    assert cliente.delete(f"{URL}/{nota['id']}", headers=cab(c["sindico"])).status_code in (404, 405)
    assert cliente.put(f"{URL}/{nota['id']}", json={"texto": "outra coisa"},
                       headers=cab(c["sindico"])).status_code in (404, 405)
    lista = cliente.get(URL, headers=cab(c["sindico"])).json()
    assert [n["texto"] for n in lista] == ["Entregador volta às 10h para o 204."]


def test_sindico_le_e_orienta(cliente, dois_porteiros):
    c = dois_porteiros
    anotar(cliente, c["porteiro"])
    r = anotar(cliente, c["sindico"], "Portão da garagem em manutenção amanhã das 8h às 12h.")
    assert r.status_code == 201
    assert len(cliente.get(URL, headers=cab(c["sindico"])).json()) == 2
    # A orientação do síndico chega aos porteiros como pendente.
    assert cliente.get(f"{URL}/pendentes", headers=cab(c["porteiro"])).json()["total"] == 1


def test_morador_nao_le_o_livro(cliente, dois_porteiros):
    c = dois_porteiros
    nota = anotar(cliente, c["porteiro"]).json()
    assert cliente.get(URL, headers=cab(c["ana"])).status_code == 403
    assert anotar(cliente, c["ana"]).status_code == 403
    assert cliente.post(f"{URL}/{nota['id']}/ciencia", headers=cab(c["ana"])).status_code == 403


def test_quem_escreveu_nao_da_ciencia_da_propria(cliente, dois_porteiros):
    c = dois_porteiros
    nota = anotar(cliente, c["porteiro"]).json()
    r = cliente.post(f"{URL}/{nota['id']}/ciencia", headers=cab(c["porteiro"]))
    assert r.status_code == 200 and r.json()["cientes"] == []


def test_passada_uma_semana_nao_e_mais_pendente(cliente, dois_porteiros, monkeypatch):
    c = dois_porteiros
    nota = anotar(cliente, c["porteiro"]).json()
    agora = livro._agora()
    monkeypatch.setattr(livro, "_agora", lambda: agora + timedelta(days=8))
    assert cliente.get(f"{URL}/pendentes", headers=cab(c["porteiro2"])).json()["total"] == 0
    lista = cliente.get(URL, headers=cab(c["porteiro2"])).json()
    assert lista[0]["id"] == nota["id"] and lista[0]["preciso_ler"] is False


def test_outro_condominio_nao_le_nem_da_ciencia(cliente, db, dois_porteiros):
    c = dois_porteiros
    nota = anotar(cliente, c["porteiro"]).json()
    outro = montar_condominio(cliente, db, nome="Outro", cnpj="11.444.777/0001-61",
                              email_sindico="s2@exemplo.com", cpf_sindico="52998224725",
                              email_admin="a2@exemplo.com", cpf_admin="16899535009")
    assert cliente.get(URL, headers=cab(outro["sindico"])).json() == []
    assert cliente.get(f"{URL}/pendentes", headers=cab(outro["sindico"])).json()["total"] == 0
    assert cliente.post(f"{URL}/{nota['id']}/ciencia",
                        headers=cab(outro["sindico"])).status_code == 404
    # E nada ficou gravado na anotação do outro condomínio.
    assert cliente.get(URL, headers=cab(c["sindico"])).json()[0]["cientes"] == []


@pytest.mark.parametrize("texto", ["", "ok", "   ", "x" * 2001])
def test_texto_invalido(cliente, dois_porteiros, texto):
    assert anotar(cliente, dois_porteiros["porteiro"], texto).status_code == 422


def test_ciencia_de_anotacao_inexistente(cliente, dois_porteiros):
    assert cliente.post(f"{URL}/999999/ciencia",
                        headers=cab(dois_porteiros["porteiro"])).status_code == 404
