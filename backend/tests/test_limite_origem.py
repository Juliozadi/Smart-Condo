"""Limite de pedidos por origem nas rotas abertas.

O código de acesso do condomínio (cerca de um milhão de combinações)
podia ser adivinhado por um script, e cada cadastro novo disparava um
e-mail ou SMS sem limite por origem.
"""
from __future__ import annotations

from tests.fixtures import montar_condominio


def test_adivinhar_o_codigo_de_acesso_e_barrado(cliente, db):
    montar_condominio(cliente, db)
    respostas = [cliente.get(f"/api/v1/condominios/por-codigo/PALM-{i:04d}").status_code
                 for i in range(25)]
    assert respostas[:20] == [404] * 20
    assert set(respostas[20:]) == {429}
    r = cliente.get("/api/v1/condominios/por-codigo/PALM-9999")
    assert r.status_code == 429 and "Retry-After" in r.headers
    assert "Aguarde um minuto" in r.json()["detalhe"]


def test_login_tem_limite_por_origem(cliente, db):
    montar_condominio(cliente, db)
    corpo = {"email": "ninguem@exemplo.com", "senha": "senhaforte123"}
    codigos = [cliente.post("/api/v1/auth/login", json=corpo).status_code for _ in range(32)]
    assert 429 in codigos and codigos.count(401) + codigos.count(403) <= 30


def test_limite_pode_ser_desligado(cliente, db, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LIMITE_POR_ORIGEM", False)
    codigos = {cliente.get(f"/api/v1/condominios/por-codigo/XXXX-{i:04d}").status_code
               for i in range(25)}
    assert codigos == {404}
