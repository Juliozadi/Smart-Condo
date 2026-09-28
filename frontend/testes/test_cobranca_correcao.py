"""O síndico corrige pela tela uma cobrança lançada errada."""
from __future__ import annotations

from conftest import abrir, ir


def test_sindico_corrige_o_valor_e_a_linha_mostra_quem(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/financeiro.html", 1500)
    botao = pg.locator("#tabelaCobrancas .btn-acao-mini").first
    botao.click()
    original = pg.input_value("#cValor")
    pg.fill("#cValor", f"{float(original) + 10:.2f}")
    pg.click("#formCorrecao button[type=submit]")
    pg.wait_for_timeout(1500)
    alterada = pg.locator("#tabelaCobrancas .table-row", has_text="Editado por Roberto Nascimento").first
    assert f"{float(original) + 10:.2f}".replace(".", ",") in alterada.inner_text()
    # Volta ao valor original.
    alterada.locator(".btn-acao-mini").click()
    pg.fill("#cValor", original)
    pg.click("#formCorrecao button[type=submit]")
    pg.wait_for_timeout(1200)
    assert pg.erros == []
    ctx.close()


def pago(titulo):
    """"Já pago: R$ 2,00 · Falta: ..." -> 2.0 (0 quando ainda não há pagamento)."""
    if not titulo or "Já pago" not in titulo:
        return 0.0
    valor = titulo.split("Já pago: R$ ")[1].split(" ·")[0]
    return float(valor.replace(".", "").replace(",", "."))


def test_sindico_registra_pagamento_recebido(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/financeiro.html", 1500)
    botao = pg.locator("#tabelaCobrancas .btn-acao-mini").last
    titulo = botao.get_attribute("title")
    linha = pg.locator("#tabelaCobrancas .table-row", has=pg.locator(f'[title="{titulo}"]'))
    pago_antes = pago(linha.get_attribute("title"))
    botao.click()
    pg.fill("#pValor", "1.00")
    pg.select_option("#pForma", "boleto")
    pg.fill("#pObservacao", "Pago no banco")
    pg.click("#btnRegistrarPagamento")
    pg.wait_for_timeout(1500)
    linha = pg.locator("#tabelaCobrancas .table-row", has=pg.locator(f'[title="{titulo}"]'))
    # Confere o aumento, e não o total: rodar de novo sem recarregar a base
    # não pode quebrar o teste.
    assert pago(linha.get_attribute("title")) == pago_antes + 1
    assert pg.erros == []
    ctx.close()
