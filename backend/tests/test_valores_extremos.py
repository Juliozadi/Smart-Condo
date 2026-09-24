"""Valores que o Pydantic aceita mas o PostgreSQL recusa.

Um id acima do limite da coluna integer e um texto com o caractere nulo
passam pela validação — são um int e um texto como outros quaisquer —, e
o banco os recusa. Antes isso virava erro 500, como se o servidor tivesse
falhado; é um dado inválido de quem chamou, e a resposta é 422.
"""
from __future__ import annotations

import pytest

from tests.fixtures import cab
from tests.test_portaria import cenario, registrar_visitante  # noqa: F401

FORA_DO_INTEGER = [2**31, -(2**31) - 1, 10**30]


@pytest.mark.parametrize("numero", FORA_DO_INTEGER)
@pytest.mark.parametrize("rota", [
    "/documentos/{}/arquivo",
    "/portaria/visitantes/{}/foto",
    "/portaria/ocorrencias/{}/foto",
])
def test_id_fora_do_limite_do_banco(cliente, cenario, rota, numero):
    r = cliente.get("/api/v1" + rota.format(numero), headers=cab(cenario["sindico"]))
    assert r.status_code == 422
    assert "detalhe" in r.json()


def test_id_fora_do_limite_no_corpo(cliente, cenario):
    r = registrar_visitante(cliente, cenario["porteiro"], 2**31)
    assert r.status_code == 422


def test_texto_com_caractere_nulo(cliente, cenario):
    r = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "Aviso\x00geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 422
    # A falha não deixa a sessão presa: a próxima requisição funciona.
    r = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "Aviso geral", "conteudo": "Conteúdo do aviso", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 201


# ── Texto só com espaços ─────────────────────────────────────────────
def test_titulo_so_com_espacos_e_recusado(cliente, cenario):
    """Antes, "   " passava pelo mínimo de 3 caracteres e virava um
    comunicado em branco, enviado a todos os moradores."""
    r = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "   ", "conteudo": "     ", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 422


def test_espacos_das_pontas_sao_aparados(cliente, cenario):
    r = cliente.post(
        "/api/v1/comunicados",
        json={"titulo": "  Aviso geral  ", "conteudo": " Conteúdo do aviso ", "categoria": "geral"},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 201
    assert r.json()["titulo"] == "Aviso geral"
    assert r.json()["conteudo"] == "Conteúdo do aviso"


def test_documento_com_titulo_so_de_espacos_e_recusado(cliente, cenario):
    r = cliente.post(
        "/api/v1/documentos",
        data={"titulo": "     ", "categoria": "ata"},
        files={"arquivo": ("ata.pdf", b"%PDF-1.4\n" + b"0" * 50, "application/pdf")},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 422


def test_senha_com_espaco_nas_pontas_continua_igual(cliente, cenario):
    """A senha é a exceção: o espaço faz parte dela."""
    r = cliente.post(
        "/api/v1/auth/senha/trocar",
        json={"senha_atual": "senhaforte123", "nova_senha": " com espaco 123 "},
        headers=cab(cenario["sindico"]),
    )
    assert r.status_code == 200, r.text
    assert cliente.post("/api/v1/auth/login", json={
        "email": "sindico@exemplo.com", "senha": " com espaco 123 "}).status_code == 200
    assert cliente.post("/api/v1/auth/login", json={
        "email": "sindico@exemplo.com", "senha": "com espaco 123"}).status_code == 401
