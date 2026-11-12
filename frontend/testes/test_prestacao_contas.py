"""Prestação de contas: o síndico lança a despesa com a nota fiscal, corrige
o valor, e o morador vê a despesa e abre o comprovante."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def test_sindico_lanca_e_morador_ve_com_comprovante(navegador):
    descricao = f"Conserto do portão {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    try:
        ir(pg, "pages/sindico/contas.html", 1500)
        pg.select_option("#dCategoria", "manutencao")
        pg.fill("#dDescricao", descricao)
        pg.fill("#dValor", "250.00")
        pg.fill("#dFornecedor", "Serralheria Ponto Certo")
        # O que não é PDF nem imagem nem sai do navegador.
        pg.set_input_files("#dComprovante", files=[
            {"name": "nota.exe", "mimeType": "application/octet-stream", "buffer": b"MZ"}])
        pg.click("#formDespesa button[type=submit]")
        assert "PDF ou uma imagem" in pg.inner_text("#erroDespesa")
        pg.set_input_files("#dComprovante", files=[
            {"name": "nota.pdf", "mimeType": "application/pdf", "buffer": PDF}])
        pg.click("#formDespesa button[type=submit]")
        pg.wait_for_selector("#erroDespesa.sucesso", timeout=8000)
        cartao = pg.locator("#listaDespesas .list-item", has_text=descricao)
        cartao.wait_for(timeout=8000)
        assert "R$ 250,00" in cartao.inner_text()
        assert cartao.locator("button", has_text="Comprovante").count() == 1

        cartao.locator("button", has_text="Corrigir").click()
        pg.fill("#eValor", "275.50")
        pg.click("#formCorrecao button[type=submit]")
        pg.locator("#listaDespesas .list-item", has_text=descricao).get_by_text(
            "R$ 275,50").wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/contas.html", 1500)
        cartao = pg.locator("#listaDespesas .list-item", has_text=descricao)
        cartao.wait_for(timeout=8000)
        assert "R$ 275,50" in cartao.inner_text()
        # O morador só vê: nada de corrigir nem cancelar.
        assert cartao.locator("button", has_text="Corrigir").count() == 0
        assert "Manutenção" in pg.inner_text("#listaCategorias")
        with pg.expect_popup() as aba:
            cartao.locator("button", has_text="Comprovante").click()
        aba.value.wait_for_selector("iframe[src^='blob:']", timeout=8000)
        assert pg.erros == []
    finally:
        for d in pg.request.get(f"{API}/financeiro/despesas", headers=sindico).json():
            if d["descricao"] == descricao:
                pg.request.post(f"{API}/financeiro/despesas/{d['id']}/cancelamento",
                                headers=sindico, data={"motivo": "Limpeza do teste"})
        ctx.close()
