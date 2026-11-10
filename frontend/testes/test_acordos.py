"""Acordo de parcelamento: o síndico junta a cobrança vencida do 302 em
parcelas e desfaz o acordo lançado errado; a Marina vê o acordo dela, com
as parcelas pagas e a que falta."""
from __future__ import annotations

from conftest import FRONT, SENHA, abrir, ir


def test_sindico_faz_e_desfaz_o_acordo(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    try:
        ir(pg, "pages/sindico/acordos.html", 1500)
        pg.select_option("#aUnidade", label="Apto 302")
        pg.locator("#aCobrancas input[type=checkbox]").first.wait_for(timeout=4000)
        pg.fill("#aParcelas", "2")
        pg.check("#aDispensar")
        pg.get_by_text("2x de cerca de", exact=False).wait_for(timeout=4000)
        pg.click("#formAcordo button[type=submit]")
        pg.wait_for_selector("#erroAcordo.sucesso", timeout=8000)
        numero = pg.inner_text("#erroAcordo").split("nº ")[1].split(" ")[0]
        cartao = pg.locator(".acordo", has_text=f"Acordo nº {numero} — apto 302")
        assert cartao.locator(".acordo-parcelas li").count() == 2
        cartao.get_by_text("Em dia", exact=True).wait_for(timeout=4000)

        # Lançado errado: desfaz, e a cobrança volta a ser devida.
        pg.once("dialog", lambda d: d.accept("Lançado no apartamento errado."))
        cartao.get_by_role("button", name=f"Desfazer o acordo nº {numero}").click()
        pg.locator(".acordo", has_text=f"Acordo nº {numero} — apto 302").get_by_text(
            "Desfeito", exact=True).wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()


def test_morador_ve_o_acordo_nas_contas(navegador):
    ctx = navegador.new_context(viewport={"width": 420, "height": 850},
                                timezone_id="America/Campo_Grande")
    pg = ctx.new_page()
    erros = []
    pg.on("pageerror", lambda e: erros.append(str(e)))
    try:
        pg.goto(f"{FRONT}/index.html")
        pg.fill("#emailInput", "marina@smartcondo.com")
        pg.fill("#senhaInput", SENHA)
        pg.click("#btnEntrar")
        pg.wait_for_url("**/morador/dashboard.html", timeout=15000)
        pg.goto(f"{FRONT}/pages/morador/financeiro.html")
        pg.locator("#secaoAcordos").wait_for(state="visible", timeout=8000)
        cartao = pg.locator("#listaAcordos .acordo").first
        assert "paga" in cartao.inner_text() and "a vencer" in cartao.inner_text()
        assert cartao.get_by_role("button").count() == 0
        pg.locator("#tabelaHistorico").get_by_text("Negociada", exact=False).first.wait_for(
            timeout=4000)
        assert erros == []
    finally:
        ctx.close()
