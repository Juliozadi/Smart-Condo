"""Foto anexada à ocorrência.

Mesmas garantias das fotos da portaria: só imagem de verdade entra, não
há endereço público, e só vê quem pode ver a ocorrência — quem abriu, o
síndico e o porteiro com a permissão de ocorrências.
"""
from __future__ import annotations

import pytest

from tests.fixtures import CPFS, cab, cadastrar_morador, cadastrar_porteiro, montar_condominio

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def cen(cliente, db):
    base = montar_condominio(cliente, db)
    _, ana = cadastrar_morador(cliente, base["sindico"], base["cond"], email="ana@exemplo.com",
                               cpf=CPFS[1], unidade="204")
    _, bruno = cadastrar_morador(cliente, base["sindico"], base["cond"], email="bruno@exemplo.com",
                                 cpf=CPFS[3], unidade="301")
    _, porteiro = cadastrar_porteiro(cliente, base["sindico"], base["cond"], cpf=CPFS[2])
    return {**base, "ana": ana, "bruno": bruno, "porteiro": porteiro}


def abrir(cliente, tok, **extra):
    corpo = {"titulo": "Vazamento na garagem", "descricao": "Água escorrendo na vaga 12."}
    corpo.update(extra)
    r = cliente.post("/api/v1/portaria/ocorrencias", json=corpo, headers=cab(tok))
    assert r.status_code == 201, r.text
    return r.json()


def anexar(cliente, tok, oid, conteudo=PNG):
    return cliente.put(f"/api/v1/portaria/ocorrencias/{oid}/foto",
                       files={"arquivo": ("foto.png", conteudo, "image/png")}, headers=cab(tok))


def test_quem_abriu_anexa_e_quem_pode_ver_ve(cliente, cen):
    o = abrir(cliente, cen["ana"])
    r = anexar(cliente, cen["ana"], o["id"])
    assert r.status_code == 200, r.text
    url = r.json()["foto_url"]
    assert url == f"/portaria/ocorrencias/{o['id']}/foto"
    for quem in ("ana", "sindico", "porteiro"):
        resp = cliente.get(f"/api/v1{url}", headers=cab(cen[quem]))
        assert resp.status_code == 200, quem
        assert resp.content == PNG
        assert "no-store" in resp.headers["cache-control"]


def test_outro_morador_e_sem_token_nao_veem(cliente, cen):
    o = abrir(cliente, cen["ana"])
    anexar(cliente, cen["ana"], o["id"])
    url = f"/api/v1/portaria/ocorrencias/{o['id']}/foto"
    assert cliente.get(url, headers=cab(cen["bruno"])).status_code == 404
    assert cliente.get(url).status_code == 401


def test_so_quem_abriu_anexa(cliente, cen):
    o = abrir(cliente, cen["ana"])
    assert anexar(cliente, cen["sindico"], o["id"]).status_code == 403
    assert anexar(cliente, cen["bruno"], o["id"]).status_code == 404


def test_depois_de_respondida_nao_troca(cliente, cen):
    o = abrir(cliente, cen["porteiro"])
    r = cliente.post(f"/api/v1/portaria/ocorrencias/{o['id']}/resposta",
                     json={"status": "em_analise", "resposta": "Encanador chamado."},
                     headers=cab(cen["sindico"]))
    assert r.status_code == 200, r.text
    assert anexar(cliente, cen["porteiro"], o["id"]).status_code == 409


def test_arquivo_que_nao_e_imagem_e_recusado(cliente, cen):
    o = abrir(cliente, cen["ana"])
    assert anexar(cliente, cen["ana"], o["id"], b"<svg onload=alert(1)>").status_code == 422


def test_endereco_livre_no_registro_e_ignorado(cliente, cen):
    o = abrir(cliente, cen["ana"], foto_url="https://rastreador.exemplo.com/pixel.png")
    assert o["foto_url"] is None
