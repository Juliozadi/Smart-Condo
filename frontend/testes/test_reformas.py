"""Obras e reformas: o João comunica a troca da fiação (a tela cobra a
ART), o síndico aprova com as condições do regimento, a portaria vê a
obra aprovada, e o João desiste dela."""
from __future__ import annotations

import random

from conftest import abrir, ir


def test_comunicar_aprovar_e_portaria_ver(navegador):
    descricao = f"Troca da fiação do quarto {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, largura=420, papel="morador")
    try:
        ir(pg, "pages/morador/reformas.html", 1500)
        pg.fill("#rDescricao", descricao)
        pg.fill("#rInicio", pg.evaluate("SmartCondo.formato.hojeIso(5)"))
        pg.fill("#rFim", pg.evaluate("SmartCondo.formato.hojeIso(12)"))
        pg.check("#rEstrutura")
        pg.click("#formReforma button[type=submit]")
        pg.get_by_text("ART ou do RRT", exact=False).last.wait_for(timeout=4000)
        pg.fill("#rResponsavel", "Eng. Paula Ramos")
        pg.fill("#rArt", "ART 1220260099999")
        pg.click("#formReforma button[type=submit]")
        pg.wait_for_selector("#erroReforma.sucesso", timeout=8000)
        pg.locator(".reforma", has_text=descricao).get_by_text("Aguardando o síndico").wait_for(
            timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="sindico")
        ir(pg, "pages/sindico/reformas.html", 1500)
        cartao = pg.locator(".reforma", has_text=descricao)
        cartao.get_by_text("Eng. Paula Ramos", exact=False).wait_for(timeout=8000)
        pg.once("dialog", lambda d: d.accept("Só das 8h às 17h; entulho em caçamba."))
        cartao.get_by_role("button", name="Aprovar a reforma do apto 204").click()
        pg.locator(".reforma", has_text=descricao).get_by_text("Condições: Só das 8h",
                                                               exact=False).wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="porteiro")
        ir(pg, "pages/porteiro/reformas.html", 1500)
        cartao = pg.locator(".reforma", has_text=descricao)
        cartao.get_by_text("Aprovada", exact=True).wait_for(timeout=8000)
        assert cartao.get_by_role("button").count() == 0
        assert pg.erros == []
        ctx.close()

        # O João desiste: a obra sai da lista da portaria.
        ctx, pg = abrir(navegador, largura=420, papel="morador")
        ir(pg, "pages/morador/reformas.html", 1500)
        pg.once("dialog", lambda d: d.accept())
        pg.locator(".reforma", has_text=descricao).get_by_role("button", name="Cancelar").click()
        pg.locator(".reforma", has_text=descricao).get_by_text("Cancelada", exact=True).wait_for(
            timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()
