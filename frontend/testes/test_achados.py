"""Achados e perdidos: a portaria registra, o morador diz "é meu" e a
portaria entrega com o nome de quem retirou já preenchido."""
from __future__ import annotations

import random

from conftest import abrir, ir


def test_portaria_registra_morador_reclama_e_portaria_entrega(navegador):
    descricao = f"Mochila azul {random.randint(10000, 99999)}"
    porteiro_ctx, porteiro = abrir(navegador, papel="porteiro")
    ir(porteiro, "pages/porteiro/achados.html", 1200)
    porteiro.fill("#aDescricao", descricao)
    porteiro.fill("#aLocal", "Hall de entrada")
    porteiro.click("#formAchado button[type=submit]")
    porteiro.locator("#erroAchado.sucesso").wait_for(timeout=8000)
    porteiro.locator(".achado", has_text=descricao).wait_for(timeout=8000)

    morador_ctx, morador = abrir(navegador, papel="morador")
    ir(morador, "pages/morador/achados.html", 1200)
    cartao = morador.locator(".achado", has_text=descricao)
    cartao.get_by_role("button", name=f"É meu: {descricao}").click()
    morador.locator(".achado", has_text=descricao).get_by_text("Você disse que é seu").wait_for(timeout=8000)
    assert "Retire na portaria" in morador.locator(".achado", has_text=descricao).inner_text()

    porteiro.reload()
    cartao = porteiro.locator(".achado", has_text=descricao)
    cartao.wait_for(timeout=8000)
    assert "Reclamado por João Silva" in cartao.inner_text()
    cartao.get_by_role("button", name=f"Entregar: {descricao}").click()
    nome = cartao.locator("input[id^=aEntregue]")
    assert nome.input_value() == "João Silva"
    cartao.locator("form button[type=submit]").click()
    porteiro.wait_for_timeout(1200)
    # Some da lista de guardados; aparece entre os entregues.
    assert porteiro.locator(".achado", has_text=descricao).count() == 0
    porteiro.select_option("#filtroAchados", "devolvido")
    porteiro.locator(".achado", has_text=descricao).get_by_text("Entregue a João Silva").wait_for(timeout=8000)

    ir(morador, "pages/morador/achados.html", 1200)
    assert "Entregue a João Silva" in morador.locator(".achado", has_text=descricao).inner_text()
    assert porteiro.erros == [] and morador.erros == []
    porteiro_ctx.close()
    morador_ctx.close()
