"""Animais de estimação: o morador cadastra, corrige e remove; o síndico
vê o animal com a situação da vacina."""
from __future__ import annotations

import random

from conftest import abrir, ir


def test_morador_cadastra_edita_e_remove(navegador):
    nome = f"Bidu {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="morador")
    ir(pg, "pages/morador/animais.html", 1200)
    pg.fill("#anNome", nome)
    pg.select_option("#anEspecie", "cao")
    pg.select_option("#anPorte", "medio")
    pg.fill("#anRaca", "Vira-lata")
    pg.click("#btnSalvarAnimal")
    pg.locator("#erroAnimal.sucesso").wait_for(timeout=8000)
    cartao = pg.locator(".animal", has_text=nome)
    cartao.wait_for(timeout=8000)
    assert "Vacina sem registro" in cartao.inner_text()

    sindico_ctx, sindico = abrir(navegador, papel="sindico")
    ir(sindico, "pages/sindico/animais.html", 1500)
    assert "Vacina sem registro" in sindico.locator(".animal", has_text=nome).inner_text()
    sindico.check("#soPendentes")
    sindico.locator(".animal", has_text=nome).wait_for(timeout=8000)
    sindico_ctx.close()

    try:
        cartao.get_by_role("button", name=f"Editar {nome}").click()
        assert pg.input_value("#anNome") == nome
        pg.fill("#anObservacao", "Tem medo de trovão")
        pg.fill("#anVacina", "2027-01-10")
        pg.click("#btnSalvarAnimal")
        pg.locator("#erroAnimal.sucesso").wait_for(timeout=8000)
        texto = pg.locator(".animal", has_text=nome).inner_text()
        assert "Tem medo de trovão" in texto and "Vacina em dia até 10/01/2027" in texto
    finally:
        pg.once("dialog", lambda d: d.accept())
        pg.locator(".animal", has_text=nome).get_by_role("button", name=f"Remover {nome}").click()
        pg.wait_for_timeout(1000)
    assert pg.locator(".animal", has_text=nome).count() == 0
    assert pg.erros == []
    ctx.close()
