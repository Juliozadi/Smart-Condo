"""Placa do carro do visitante.

A API passou a normalizar a placa do visitante como a do pátio (ABC1D23)
e a recusar a incompleta. A tela avisa antes de enviar, e o morador vê a
placa no formato de sempre (ABC-1D23).
"""
from __future__ import annotations

import random

from conftest import abrir, ir
from test_arquivos import cpf_valido


def _preencher(pg, nome, placa):
    pg.fill("#nome-visitante", nome)
    pg.fill("#doc-visitante", cpf_valido())
    pg.select_option("#apto-visitante", label="204")
    pg.select_option("#tipo-visita", index=1)
    pg.fill("#placa-visitante", "")
    pg.type("#placa-visitante", placa)


def test_placa_incompleta_e_avisada_e_a_completa_chega_ao_morador(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    ir(pg, "pages/porteiro/visitantes.html", 1200)
    enviados = []
    pg.on("request", lambda r: r.method == "POST" and r.url.endswith("/portaria/visitantes")
          and enviados.append(r.url))
    nome = f"Visitante Placa {random.randint(1000, 9999)}"

    _preencher(pg, nome, "abc12")
    pg.click("#formVisitante button[type=submit]")
    assert "7 letras ou números" in pg.inner_text("#erroVisitante")
    assert enviados == []

    _preencher(pg, nome, "abc1d23")
    assert pg.input_value("#placa-visitante") == "ABC-1D23"
    pg.click("#formVisitante button[type=submit]")
    pg.wait_for_selector("#erroVisitante.sucesso", timeout=10000)
    assert len(enviados) == 1
    assert pg.erros == []
    ctx.close()

    ctx, pg = abrir(navegador, papel="morador")
    item = pg.locator(".portaria-item", has_text=nome)
    item.wait_for(timeout=8000)
    assert "placa ABC-1D23" in item.inner_text()
    ctx.close()
