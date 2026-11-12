"""Advertências e multas: o síndico notifica pela tela, o morador se
defende no prazo, e o síndico decide com o motivo."""
from __future__ import annotations

import random

from conftest import FRONT, SENHA, abrir, ir


def entrar_como(navegador, email, largura=420):
    """Uma aba logada com outro morador da demonstração (o Bruno, do 102)."""
    ctx = navegador.new_context(viewport={"width": largura, "height": 850},
                                timezone_id="America/Campo_Grande")
    pg = ctx.new_page()
    pg.erros = []
    pg.on("pageerror", lambda e: pg.erros.append(str(e)))
    pg.goto(f"{FRONT}/index.html")
    pg.fill("#emailInput", email)
    pg.fill("#senhaInput", SENHA)
    pg.click("#btnEntrar")
    pg.wait_for_url("**/morador/dashboard.html", timeout=15000)
    return ctx, pg


def test_notificacao_defesa_e_decisao(navegador):
    marca = f"Bicicleta na escada de incêndio, teste {random.randint(1000, 9999)}."
    ctx, pg = abrir(navegador, papel="sindico")
    try:
        ir(pg, "pages/sindico/infracoes.html", 1500)
        pg.select_option("#iUnidade", label="Apto 102")
        pg.select_option("#iTipo", "advertencia")
        assert not pg.is_visible("#iValor")
        pg.fill("#iArtigo", "Regimento interno, art. 7")
        pg.fill("#iDescricao", marca)
        pg.click("#formInfracao button[type=submit]")
        pg.wait_for_selector("#erroInfracao.sucesso", timeout=8000)
        pg.locator("#listaAguardando .infracao", has_text=marca).wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = entrar_como(navegador, "bruno@smartcondo.com")
        ir(pg, "pages/morador/infracoes.html", 1500)
        cartao = pg.locator(".infracao", has_text=marca)
        cartao.wait_for(timeout=8000)
        cartao.locator("textarea").fill("A bicicleta é do vizinho do 101; a nossa fica na garagem.")
        pg.once("dialog", lambda d: d.accept())
        cartao.get_by_role("button", name="Enviar a defesa").click()
        pg.locator(".infracao", has_text=marca).get_by_text("Defesa em análise").wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="sindico")
        ir(pg, "pages/sindico/infracoes.html", 1500)
        cartao = pg.locator("#listaDecidir .infracao", has_text=marca)
        cartao.wait_for(timeout=8000)
        assert "A bicicleta é do vizinho do 101" in cartao.inner_text()
        pg.once("dialog", lambda d: d.accept("A bicicleta é mesmo do 101."))
        cartao.get_by_role("button", name="Anular a notificação do apto 102", exact=False).click()
        pg.locator("#listaHistorico .infracao", has_text=marca).get_by_text("Anulada").first \
            .wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()
