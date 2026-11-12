"""Livro da portaria: a Renata passa o turno com um aviso importante; o
Carlos chega, vê no painel que tem o que ler e dá ciência; o síndico vê
quem já leu."""
from __future__ import annotations

import random

from conftest import FRONT, SENHA, abrir, ir


def entrar_como_porteiro(navegador, email, largura=420):
    ctx = navegador.new_context(viewport={"width": largura, "height": 850},
                                timezone_id="America/Campo_Grande")
    pg = ctx.new_page()
    pg.erros = []
    pg.on("pageerror", lambda e: pg.erros.append(str(e)))
    pg.goto(f"{FRONT}/index.html")
    pg.fill("#emailInput", email)
    pg.fill("#senhaInput", SENHA)
    pg.click("#btnEntrar")
    pg.wait_for_url("**/porteiro/dashboard.html", timeout=15000)
    return ctx, pg


def test_passagem_de_turno_pela_tela(navegador):
    marca = f"O entregador volta às 10h para o 204, teste {random.randint(1000, 9999)}."
    ctx, pg = entrar_como_porteiro(navegador, "renata@smartcondo.com")
    try:
        ir(pg, "pages/porteiro/livro.html", 1200)
        pg.fill("#lTexto", marca)
        pg.check("#lImportante")
        pg.click("#formLivro button[type=submit]")
        pg.wait_for_selector("#erroLivro.sucesso", timeout=8000)
        # Quem escreveu não precisa dar ciência da própria anotação.
        cartao = pg.locator("#listaLivro .anotacao", has_text=marca)
        cartao.wait_for(timeout=8000)
        assert "Ninguém deu ciência ainda." in cartao.inner_text()
        assert cartao.get_by_role("button").count() == 0
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, largura=420, papel="porteiro")
        pg.wait_for_selector("#livroPendentes:not([hidden])", timeout=8000)
        ir(pg, "pages/porteiro/livro.html", 1200)
        cartao = pg.locator("#listaLer .anotacao", has_text=marca)
        cartao.wait_for(timeout=8000)
        cartao.get_by_role("button", name="Dar ciência", exact=False).click()
        lido = pg.locator("#listaLivro .anotacao", has_text=marca)
        lido.get_by_text("Ciente: Carlos Pereira", exact=False).wait_for(timeout=8000)
        assert pg.locator("#listaLer .anotacao", has_text=marca).count() == 0
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="sindico")
        pg.wait_for_selector("#textoPendencias:has-text('livro da portaria')", timeout=8000)
        ir(pg, "pages/sindico/livro.html", 1200)
        cartao = pg.locator(".anotacao", has_text=marca)
        cartao.wait_for(timeout=8000)
        assert "Ciente: Carlos Pereira" in cartao.inner_text()
        assert pg.erros == []
    finally:
        ctx.close()


def test_morador_nao_abre_o_livro(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    try:
        pg.goto(f"{FRONT}/pages/porteiro/livro.html")
        pg.wait_for_url("**/morador/dashboard.html", timeout=8000)
        pg.goto(f"{FRONT}/pages/sindico/livro.html")
        pg.wait_for_url("**/morador/dashboard.html", timeout=8000)
    finally:
        ctx.close()
