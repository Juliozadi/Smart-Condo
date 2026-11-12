"""Visitante e encomenda para um apartamento sem morador no sistema.

Situação real: o apartamento está vazio, à venda, ou o morador se mudou e
o novo ainda não se cadastrou. A portaria registrava o visitante, o aviso
não chegava a ninguém, e ele esperava duas horas por uma confirmação que
nunca viria; a encomenda do antigo morador ficava na portaria sem que
ninguém soubesse.
"""
from __future__ import annotations

import pytest

from app.services import notificacao
from tests.fixtures import cab
from tests.test_portaria import (  # noqa: F401
    DOC_VISITANTE, cenario, registrar_encomenda, registrar_visitante,
)


@pytest.fixture
def avisados(monkeypatch):
    lista = []
    monkeypatch.setattr(notificacao, "notificar",
                        lambda destino, canal, titulo, mensagem: lista.append((destino, mensagem)))
    return lista


@pytest.fixture
def vazia(cliente, cenario):
    """Uma unidade cadastrada pelo síndico, onde ninguém mora."""
    r = cliente.post("/api/v1/condominios/meu/unidades", headers=cab(cenario["sindico"]),
                     json={"numero": "502"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_visitante_nao_fica_esperando_quem_nao_existe(cliente, cenario, vazia, avisados):
    r = registrar_visitante(cliente, cenario["porteiro"], vazia)
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["sem_morador"] is True
    assert v["status"] == "sem_resposta"
    # Quem fica sabendo é o síndico.
    assert [d for d, _ in avisados] == ["sindico@exemplo.com"]
    assert "502" in avisados[0][1]


def test_encomenda_para_apartamento_vazio_avisa_o_sindico(cliente, cenario, vazia, avisados):
    r = registrar_encomenda(cliente, cenario["porteiro"], vazia)
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["sem_morador"] is True and e["status"] == "aguardando_retirada"
    assert [d for d, _ in avisados] == ["sindico@exemplo.com"]


def test_com_morador_nada_muda(cliente, cenario, avisados):
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u204"]).json()
    assert v["sem_morador"] is False and v["status"] == "aguardando_confirmacao"
    e = registrar_encomenda(cliente, cenario["porteiro"], cenario["u204"]).json()
    assert e["sem_morador"] is False
    assert [d for d, _ in avisados] == ["ana@exemplo.com", "ana@exemplo.com"]


def test_morador_que_se_mudou_deixa_o_apartamento_vazio(cliente, cenario, avisados):
    bruno = next(u for u in cliente.get("/api/v1/usuarios", headers=cab(cenario["sindico"])).json()
                 if u["email"] == "bruno@exemplo.com")
    assert cliente.delete(f"/api/v1/usuarios/{bruno['id']}",
                          headers=cab(cenario["sindico"])).status_code == 200
    avisados.clear()
    v = registrar_visitante(cliente, cenario["porteiro"], cenario["u301"]).json()
    assert v["sem_morador"] is True and v["status"] == "sem_resposta"
    assert [d for d, _ in avisados] == ["sindico@exemplo.com"]


def test_portaria_ve_quais_unidades_estao_sem_morador(cliente, cenario, vazia):
    unidades = {u["id"]: u for u in cliente.get("/api/v1/condominios/meu/unidades",
                                                headers=cab(cenario["porteiro"])).json()}
    assert unidades[vazia]["sem_morador"] is True
    assert unidades[cenario["u204"]]["sem_morador"] is False
    # O morador não precisa saber quais apartamentos estão vazios.
    do_morador = cliente.get("/api/v1/condominios/meu/unidades", headers=cab(cenario["ana"])).json()
    assert all(u["sem_morador"] is None for u in do_morador)
