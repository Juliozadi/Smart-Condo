"""Login de quem ainda não pode entrar: a tela leva ao passo certo.

Quem não confirmou o código ficava só com a mensagem, sem caminho até a
confirmação; o cadastro recusado via "indisponível", sem o motivo.
"""
from __future__ import annotations

import random

from conftest import FRONT, abrir
from test_administradores import cpf_valido

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"
SENHA = "senhaforte123"


def cadastrar_morador(pg):
    cab = {"Authorization": "Bearer " + pg.request.post(f"{API}/auth/login", data={
        "email": "sindico@smartcondo.com", "senha": "smartcondo123"}).json()["access_token"]}
    codigo = pg.request.get(f"{API}/condominios/meu", headers=cab).json()["codigo_acesso"]
    email = f"novo{random.randint(10000, 99999)}@exemplo.com"
    r = pg.request.post(f"{API}/auth/cadastro/morador", data={
        "nome": "Morador Novo", "email": email, "cpf": cpf_valido(),
        "telefone": "(67) 99999-1234", "senha": SENHA, "codigo_condominio": codigo,
        "unidade_numero": "302", "tipo_ocupacao": "inquilino"})
    assert r.ok, r.text()
    return email, r.json(), cab


def entrar(pg, email):
    pg.goto(f"{FRONT}/index.html")
    pg.fill("#emailInput", email)
    pg.fill("#senhaInput", SENHA)
    pg.click("#btnEntrar")


def test_sem_codigo_confirmado_vai_para_a_confirmacao(navegador):
    ctx, pg = abrir(navegador)
    email, _, _ = cadastrar_morador(pg)
    entrar(pg, email)
    pg.wait_for_url("**/cadastro/confirmar_codigo.html", timeout=8000)
    # Vindo do login, o reenvio já está liberado.
    assert pg.inner_text("#reenviarCadastro").strip().lower().startswith("reenviar")
    assert pg.erros == []
    ctx.close()


def test_recusado_ve_o_motivo(navegador):
    ctx, pg = abrir(navegador)
    email, corpo, cab = cadastrar_morador(pg)
    pg.request.post(f"{API}/auth/confirmar", data={"email": email, "codigo": corpo["codigo_debug"]})
    pg.request.post(f"{API}/usuarios/{corpo['usuario']['id']}/aprovacao", headers=cab,
                    data={"aprovado": False, "motivo": "Unidade não confere"})
    entrar(pg, email)
    pg.locator("#erroLogin.visivel").wait_for(timeout=5000)
    assert "Motivo: Unidade não confere" in pg.inner_text("#erroLogin")
    ctx.close()
