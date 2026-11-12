"""Rateio pela fração ideal e cota extra, pela tela do síndico.

A tabela de unidades mostra a fração de cada apartamento e avisa quando
elas não somam 100%; a tela financeira lança a cota extra para o prédio
inteiro num pedido só, com cada um pagando a sua parte.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def _editar_fracao(pg, numero, valor):
    linha = pg.locator("#tabelaUnidades .table-row", has_text=numero).first
    linha.get_by_role("button", name=f"Editar unidade {numero}").click()
    pg.fill("#uFracao", valor)
    pg.click("#formUnidade button[type=submit]")
    pg.wait_for_timeout(1000)


def test_sindico_ve_a_fracao_e_o_aviso_da_soma(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/moradores.html", 1500)
    linha = pg.locator("#tabelaUnidades .table-row", has_text="302").first
    original = linha.locator("span").nth(3).inner_text()
    assert original == "13,5%"
    assert pg.inner_text("#somaFracoes") == "As frações ideais somam 100%."
    try:
        _editar_fracao(pg, "302", "14")
        assert pg.inner_text("#somaFracoes") == \
            "As frações ideais somam 100,5% — precisam somar 100% para o rateio."
        linha = pg.locator("#tabelaUnidades .table-row", has_text="302").first
        assert linha.locator("span").nth(3).inner_text() == "14%"
    finally:
        # Volta como estava, para não mexer nos outros testes.
        _editar_fracao(pg, "302", "13.5")
    assert pg.inner_text("#somaFracoes") == "As frações ideais somam 100%."
    assert pg.erros == []
    ctx.close()


def test_sindico_lanca_cota_extra_pela_fracao(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    ir(pg, "pages/sindico/financeiro.html", 1500)
    pg.select_option("#fin_tipo", "extra")
    pg.select_option("#fin_rateio", "fracao")
    # Um apartamento só não divide nada: a escolha some, e as parcelas aparecem.
    assert pg.is_disabled("#fin_unidade")
    assert pg.is_visible("#fin_parcelas")
    assert pg.inner_text("#rotuloValor") == "Total do condomínio (R$)"

    # Competência antiga e vencimento à frente: nada fica em atraso.
    hoje = datetime.now(ZoneInfo("America/Campo_Grande")).date()
    ano, mes = divmod(hoje.year * 12 + hoje.month - 1 - random.randint(24, 55), 12)
    descricao = f"Pintura da fachada {random.randint(10000, 99999)}"
    pg.fill("#fin_competencia", date(ano, mes + 1, 1).strftime("%Y-%m"))
    pg.fill("#fin_valor", "1000.00")
    pg.fill("#fin_descricao", descricao)
    pg.fill("#fin_parcelas", "2")
    pg.fill("#fin_vencimento", (hoje + timedelta(days=20)).isoformat())
    lancadas = []
    try:
        pg.click("#formCobranca button[type=submit]")
        pg.locator("#erroCobranca.sucesso").wait_for(timeout=8000)
        assert pg.inner_text("#erroCobranca") == "14 cobranças geradas, R$ 1.000,00."
        lancadas = [c for c in pg.request.get(f"{API}/financeiro/cobrancas", headers=sindico).json()
                    if c["descricao"].startswith(descricao)]
        do_302 = sorted((c for c in lancadas if c["unidade"].endswith("302")),
                        key=lambda c: c["vencimento"])
        # 13,5% de R$ 1.000,00 = R$ 135,00, em duas de R$ 67,50.
        assert [c["valor"] for c in do_302] == ["67.50", "67.50"]
        assert [c["descricao"] for c in do_302] == [
            f"{descricao} — parcela 1/2", f"{descricao} — parcela 2/2"]
        assert all(c["origem"] == "extra" and c["status"] == "aberta" for c in lancadas)
        assert len(lancadas) == 14
    finally:
        # Cancela o que o teste lançou: as outras telas não contam com isso.
        for c in lancadas:
            r = pg.request.post(f"{API}/financeiro/cobrancas/{c['id']}/cancelamento",
                                headers=sindico, data={"motivo": "Lançada pelo teste de tela"})
            assert r.ok, r.text()
    assert pg.erros == []
    ctx.close()
