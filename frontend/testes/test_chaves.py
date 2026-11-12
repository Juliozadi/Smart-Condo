"""Quadro de chaves: a portaria entrega e recebe a chave do salão; a cópia
do 204 só sai para a Rosa, a diarista que o João autorizou, e só com o
CPF dela; o João vê no SmartCondo com quem a chave está."""
from __future__ import annotations

import random

from conftest import abrir, ir


def cartao(pg, nome):
    return pg.locator(".chave", has_text=nome)


def test_chave_de_area_comum(navegador):
    nome = f"Depósito de jardinagem {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="porteiro")
    try:
        ir(pg, "pages/porteiro/chaves.html", 1500)
        pg.fill("#cNome", nome)
        pg.fill("#cPosicao", "D4")
        pg.click("#formChave button[type=submit]")
        pg.wait_for_selector("#erroChave.sucesso", timeout=8000)

        cartao(pg, nome).get_by_role("button", name=f"Entregar a chave {nome}").click()
        pg.fill(f"#{cartao(pg, nome).locator('input').first.get_attribute('id')}", "Seu Antônio, jardineiro")
        cartao(pg, nome).get_by_role("button", name="Entregar a chave", exact=True).click()
        cartao(pg, nome).get_by_text("Com Seu Antônio, jardineiro", exact=False).wait_for(timeout=8000)

        cartao(pg, nome).get_by_role("button", name=f"Recebi de volta a chave {nome}").click()
        cartao(pg, nome).get_by_text("Na portaria", exact=True).wait_for(timeout=8000)
        cartao(pg, nome).get_by_role("button", name=f"Histórico da chave {nome}").click()
        cartao(pg, nome).get_by_text("Devolvida em", exact=False).wait_for(timeout=8000)

        pg.once("dialog", lambda d: d.accept())
        cartao(pg, nome).get_by_role("button", name=f"Remover a chave {nome}").click()
        cartao(pg, nome).wait_for(state="detached", timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()


def test_chave_do_apartamento_so_com_o_cpf_da_autorizada(navegador):
    nome = "Apto 204 — cópia"
    ctx, pg = abrir(navegador, papel="porteiro")
    try:
        ir(pg, "pages/porteiro/chaves.html", 1500)
        # Na demonstração, a cópia está com a Rosa: primeiro ela volta.
        voltou = cartao(pg, nome).get_by_role("button", name=f"Recebi de volta a chave {nome}")
        if voltou.count():
            voltou.click()
            cartao(pg, nome).get_by_text("Na portaria", exact=True).wait_for(timeout=8000)

        cartao(pg, nome).get_by_role("button", name=f"Entregar a chave {nome}").click()
        cartao(pg, nome).get_by_label("Rosa Lima", exact=False).check()
        cpf = cartao(pg, nome).get_by_label("CPF do documento apresentado")
        cpf.fill("529.982.247-25")
        cartao(pg, nome).get_by_role("button", name="Entregar a chave", exact=True).click()
        cartao(pg, nome).get_by_text("não confere", exact=False).wait_for(timeout=8000)

        cpf.fill("619.326.751-40")
        cartao(pg, nome).get_by_role("button", name="Entregar a chave", exact=True).click()
        cartao(pg, nome).get_by_text("Com Rosa Lima", exact=False).wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        # O João vê com quem está a chave do apartamento dele.
        ctx, pg = abrir(navegador, largura=420, papel="morador")
        ir(pg, "pages/morador/visitantes.html", 1500)
        pg.locator("#listaChaves").get_by_text("Com Rosa Lima", exact=False).wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()
