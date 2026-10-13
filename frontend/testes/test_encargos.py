"""Multa e juros da cobrança paga com atraso.

O morador vê o valor de hoje, com a multa e os juros, e paga esse valor;
o síndico define os percentuais e, num acordo, dispensa os encargos.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def _token(pg, email):
    r = pg.request.post(f"{API}/auth/login", data={"email": email, "senha": "smartcondo123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def _cobranca_vencida(pg, sindico, unidade_id, descricao):
    """R$ 300,00 vencida há 10 dias, numa competência antiga e livre."""
    # "Hoje" no fuso do condomínio, como a API conta o atraso.
    hoje = datetime.now(ZoneInfo("America/Campo_Grande")).date()
    vencimento = hoje - timedelta(days=10)
    for _ in range(20):
        meses = random.randint(24, 55)
        ano, mes = divmod(hoje.year * 12 + hoje.month - 1 - meses, 12)
        r = pg.request.post(f"{API}/financeiro/cobrancas", headers=sindico, data={
            "unidade_id": unidade_id, "competencia": date(ano, mes + 1, 1).isoformat(),
            "descricao": descricao, "valor": "300.00", "vencimento": vencimento.isoformat()})
        if r.status != 409:
            assert r.ok, r.text()
            return r.json()
    raise AssertionError("nenhuma competência livre")


def test_morador_paga_com_multa_e_juros(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    sindico = _token(pg, "sindico@smartcondo.com")
    morador = _token(pg, "morador@smartcondo.com")
    unidade_id = pg.request.get(f"{API}/auth/eu", headers=morador).json()["unidade"]["id"]
    descricao = f"Taxa extra {random.randint(1000, 9999)}"
    _cobranca_vencida(pg, sindico, unidade_id, descricao)

    ir(pg, "pages/morador/financeiro.html", 1500)
    cartao = pg.locator("#listaAbertas .list-item", has_text=descricao)
    cartao.wait_for(timeout=8000)
    texto = cartao.inner_text()
    assert "multa de R$ 6,00" in texto and "juros de R$ 1,00" in texto, texto
    pg.once("dialog", lambda d: d.accept())
    cartao.get_by_role("button", name="Pagar R$ 307,00").click()
    pg.wait_for_selector("#erroPagamento.sucesso", timeout=8000)
    cartao.wait_for(state="detached", timeout=8000)
    assert pg.erros == []
    ctx.close()


def test_sindico_dispensa_os_encargos_pela_tela(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = _token(pg, "sindico@smartcondo.com")
    morador = _token(pg, "morador@smartcondo.com")
    unidade_id = pg.request.get(f"{API}/auth/eu", headers=morador).json()["unidade"]["id"]
    descricao = f"Taxa acordo {random.randint(1000, 9999)}"
    cobranca = _cobranca_vencida(pg, sindico, unidade_id, descricao)

    ir(pg, "pages/sindico/financeiro.html", 1500)
    assert pg.input_value("#encMulta") == "2.00" and pg.input_value("#encJuros") == "1.00"
    linha = pg.locator("#tabelaCobrancas .table-row", has_text=descricao)
    linha.locator(".btn-acao-mini").click()
    assert pg.input_value("#pValor") == "307.00"
    assert "multa de R$ 6,00" in pg.inner_text("#pEncargos")
    pg.check("#pDispensar")
    assert pg.input_value("#pValor") == "300.00"
    pg.click("#btnRegistrarPagamento")
    linha.get_by_text("Paga").wait_for(timeout=8000)
    assert "Editado por" in linha.inner_text()
    registrada = next(c for c in pg.request.get(f"{API}/financeiro/cobrancas", headers=sindico).json()
                      if c["id"] == cobranca["id"])
    assert registrada["ultima_alteracao"]["descricao"] == "Dispensou R$ 7.00 de multa e juros"
    assert pg.erros == []
    ctx.close()


def test_percentuais_fora_da_lei_sao_avisados(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/financeiro.html", 1500)
    pg.fill("#encMulta", "10")
    pg.click("#formEncargos button[type=submit]")
    assert "de 0 a 2%" in pg.inner_text("#erroEncargos")
    assert pg.erros == []
    ctx.close()
