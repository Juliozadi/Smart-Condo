"""Veículos do apartamento: o morador cadastra a placa pela tela e, na
portaria, digitar a placa já mostra o apartamento e preenche o formulário."""
from __future__ import annotations

import random
import string

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_morador_cadastra_e_portaria_reconhece(navegador):
    placa = ("".join(random.choices(string.ascii_uppercase, k=3)) + str(random.randint(0, 9)) +
             random.choice(string.ascii_uppercase) + f"{random.randint(0, 99):02d}")
    legivel = placa[:3] + "-" + placa[3:]
    ctx, pg = abrir(navegador, papel="morador")
    morador = token_da_aba(pg)
    try:
        ir(pg, "pages/morador/veiculos.html", 1500)
        # O carro de demonstração do 204 já está na lista.
        pg.locator("#listaVeiculos .placa-cadastrada", has_text="RIO-2A18").wait_for(timeout=8000)
        # Placa incompleta não sai da tela.
        pg.fill("#vPlaca", "AB12")
        pg.click("#formVeiculo button[type=submit]")
        pg.get_by_text("A placa precisa ter 7").wait_for(timeout=4000)

        pg.fill("#vPlaca", placa)
        pg.fill("#vModelo", "Fusca")
        pg.fill("#vCor", "Azul")
        pg.click("#formVeiculo button[type=submit]")
        pg.wait_for_selector("#erroVeiculo.sucesso", timeout=8000)
        item = pg.locator("#listaVeiculos .list-item", has_text=legivel)
        item.wait_for(timeout=8000)
        assert "Fusca · Azul" in item.inner_text()
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="porteiro")
        ir(pg, "pages/porteiro/veiculos.html", 1500)
        pg.fill("#veicul_placaDoVeiculo", placa)
        pg.get_by_text("Cadastrado: Apto 204 · Fusca Azul").wait_for(timeout=8000)
        assert pg.input_value("#veicul_tipoDeMovimentacao") == "entrada|morador"
        rotulo = pg.eval_on_selector(
            "#veicul_apartamento", "s => s.options[s.selectedIndex].textContent")
        assert rotulo == "Apto 204", rotulo
        assert pg.input_value("#veicul_modelo") == "Fusca Azul"
        # Placa de fora: avisa que não é de nenhum apartamento.
        pg.fill("#veicul_placaDoVeiculo", "ZZZ9Z99")
        pg.get_by_text("Placa não cadastrada por nenhum apartamento.").wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        for v in pg.request.get(f"{API}/veiculos/cadastrados", headers=morador).json():
            if v["placa"] == placa:
                pg.request.delete(f"{API}/veiculos/cadastrados/{v['id']}", headers=morador)
        ctx.close()
