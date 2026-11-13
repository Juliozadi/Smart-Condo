"""Medição de água e gás: o síndico lança a leitura do mês, vê o consumo
enquanto digita e gera a cobrança pela tarifa; o morador vê o histórico."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_sindico_lanca_a_leitura_e_cobra_o_consumo(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    ir(pg, "pages/sindico/consumo.html", 1500)
    linha = pg.locator("#tabelaLeituras .table-row", has_text="Apto 204")
    anterior = float(linha.locator(":scope > span").nth(1).inner_text().split(" m³")[0]
                     .replace(".", "").replace(",", "."))
    consumo = random.randint(5, 20)
    pg.fill("input[aria-label='Leitura do apto 204']", str(int(anterior) + consumo))
    assert linha.locator(".leitura-consumo").inner_text() == f"{consumo} m³"
    pg.click("#btnSalvarLeituras")
    pg.locator("#erroLeituras.sucesso").wait_for(timeout=8000)
    assert "1 leitura salva" in pg.inner_text("#erroLeituras")
    criadas = []
    try:
        pg.fill("#cTarifa", "10")
        pg.click("#formCobrar button[type=submit]")
        pg.locator("#erroCobrar.sucesso").wait_for(timeout=8000)
        assert f"1 cobrança gerada, R$ {consumo * 10},00" in pg.inner_text("#erroCobrar")
        linha = pg.locator("#tabelaLeituras .table-row", has_text="Apto 204")
        assert f"Cobrada: R$ {consumo * 10},00" in linha.inner_text()
        assert linha.locator("input[type=number]").is_disabled()
        criadas = [c for c in pg.request.get(f"{API}/financeiro/cobrancas", headers=sindico).json()
                   if c["origem"] == "consumo" and c["status"] in ("aberta", "vencida")]
        assert len(criadas) == 1 and criadas[0]["unidade"].endswith("204")
    finally:
        # A cobrança do teste sai; a leitura fica, e volta a poder ser
        # corrigida na próxima vez.
        for c in criadas:
            pg.request.post(f"{API}/financeiro/cobrancas/{c['id']}/cancelamento", headers=sindico,
                            data={"motivo": "Lançada pelo teste de tela"})
    assert pg.erros == []
    ctx.close()


def test_morador_ve_o_historico(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    ir(pg, "pages/morador/dashboard.html", 1000)
    pg.click("a[href='consumo.html']")
    pg.locator("#tabela-agua .table-row").first.wait_for(timeout=8000)
    assert pg.locator("#tabela-agua .table-row").count() >= 4
    assert "primeira leitura" in pg.inner_text("#tabela-agua")
    assert pg.erros == []
    ctx.close()
