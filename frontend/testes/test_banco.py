"""Tela "Banco de dados" do síndico: o que as visões, a função de rateio e o
gatilho de log das cobranças devolvem, dentro do sistema."""
from __future__ import annotations

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_sindico_ve_visoes_rateio_e_log_do_gatilho(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/dashboard.html", 1000)
    pg.click("a[href='banco.html']")
    pg.locator("#tabelaSituacao .table-row").first.wait_for(timeout=8000)
    assert pg.locator("#tabelaSituacao .table-row").count() == 7
    assert pg.locator("#tabelaBalancete .table-row").count() >= 1
    # Rateio calculado pela função do banco: a soma fecha no centavo.
    pg.fill("#rTotal", "1000.01")
    pg.click("#formRateio button[type=submit]")
    pg.locator("#tabelaRateio .rateio-soma").wait_for(timeout=8000)
    assert "R$ 1.000,01" in pg.inner_text("#tabelaRateio .rateio-soma")
    # Uma correção de valor pela API vira uma linha do log, escrita pelo gatilho.
    sindico = token_da_aba(pg)
    alvo = next(c for c in pg.request.get(f"{API}/financeiro/cobrancas", headers=sindico).json()
                if c["status"] == "aberta")
    original = alvo["valor"]
    novo = f"{float(original) + 1:.2f}"
    try:
        r = pg.request.put(f"{API}/financeiro/cobrancas/{alvo['id']}", headers=sindico,
                           data={"valor": novo})
        assert r.ok, r.text()
        pg.reload()
        pg.locator("#tabelaLog .table-row").first.wait_for(timeout=8000)
        assert alvo["descricao"] in pg.locator("#tabelaLog .table-row").first.inner_text()
    finally:
        r = pg.request.put(f"{API}/financeiro/cobrancas/{alvo['id']}", headers=sindico,
                           data={"valor": original})
        assert r.ok, r.text()
    assert pg.erros == []
    ctx.close()
