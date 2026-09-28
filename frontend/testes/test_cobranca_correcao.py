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
