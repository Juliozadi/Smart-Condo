"""Apartamento sem morador no sistema: a portaria fica sabendo ao escolher
a unidade, o visitante não fica esperando e o síndico é avisado."""
from __future__ import annotations

import random

from conftest import abrir, ir
from test_arquivos import cpf_valido


def _escolher_vazio(pg, seletor):
    vazio = pg.locator(f"{seletor} option[data-sem-morador]").first
    pg.select_option(seletor, vazio.get_attribute("value"))
    return vazio.get_attribute("data-identificacao")


def test_visitante_e_encomenda_para_apartamento_vazio(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    ir(pg, "pages/porteiro/visitantes.html", 1500)
    nome = f"Corretor {random.randint(1000, 9999)}"

    pg.select_option("#apto-visitante", label="204")
    assert pg.locator("#avisoSemMorador").is_hidden()
    apto = _escolher_vazio(pg, "#apto-visitante")
    assert f"Ninguém mora no apto {apto}" in pg.inner_text("#avisoSemMorador")

    pg.fill("#nome-visitante", nome)
    pg.fill("#doc-visitante", cpf_valido())
    pg.select_option("#tipo-visita", index=1)
    pg.click("#formVisitante button[type=submit]")
    pg.locator("#erroVisitante", has_text="O síndico foi avisado").wait_for(timeout=8000)
    pg.locator("#tabelaHistorico .table-row", has_text=nome).get_by_text("Sem resposta").wait_for(
        timeout=8000)
    assert pg.locator("#avisoSemMorador").is_hidden()
    assert pg.erros == []

    ir(pg, "pages/porteiro/encomendas.html", 1500)
    _escolher_vazio(pg, "#encome_destinatarioApartamento")
    assert pg.locator("#avisoSemMorador").is_visible()
    pg.select_option("#encome_remetenteTransportadora", index=1)
    pg.select_option("#encome_tipoDeVolume", index=1)
    pg.click("#formEncomenda button[type=submit]")
    pg.locator("#erroEncomenda", has_text="o síndico foi avisado").wait_for(timeout=8000)
    assert pg.erros == []
    ctx.close()
