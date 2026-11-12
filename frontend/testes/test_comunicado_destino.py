"""Comunicado só para um apartamento: a advertência que não é da conta
dos vizinhos nem da portaria."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_advertencia_chega_so_ao_apartamento(navegador):
    titulo = f"Advertência {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="morador")
    unidade = pg.request.get(f"{API}/auth/eu", headers=token_da_aba(pg)).json()["unidade"]
    ctx.close()

    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    try:
        ir(pg, "pages/sindico/comunicados.html", 1500)
        assert pg.locator("#grupoAlvo").is_hidden()
        pg.fill("#comuni_tituloDoComunicado", titulo)
        pg.select_option("#comuni_categoria", "geral")
        pg.select_option("#comuni_destino", "unidade")
        assert "Nem os vizinhos nem a portaria" in pg.inner_text("#textoDestino")
        pg.select_option("#comuni_alvo", str(unidade["id"]))
        pg.fill("#comuni_mensagem", "Barulho depois das 22h no dia 10/10.")
        pg.click("#formComunicado button[type=submit]")
        pg.wait_for_selector("#erroComunicado.sucesso", timeout=8000)
        linha = pg.locator("#tabelaComunicados .table-row", has_text=titulo)
        assert "Só para: Apto " + unidade["numero"] in linha.inner_text()
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/comunicados.html", 1500)
        cartao = pg.locator("#listaComunicados .comunicado-item", has_text=titulo)
        cartao.wait_for(timeout=8000)
        assert "Só para o seu apartamento" in cartao.inner_text()
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="porteiro")
        vistos = [c["titulo"] for c in pg.request.get(f"{API}/comunicados",
                                                       headers=token_da_aba(pg)).json()]
        assert titulo not in vistos
    finally:
        for c in pg.request.get(f"{API}/comunicados", headers=sindico).json():
            if c["titulo"] == titulo:
                pg.request.delete(f"{API}/comunicados/{c['id']}", headers=sindico)
        ctx.close()
