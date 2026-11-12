"""Assembleia virtual: o síndico convoca pela tela, o morador vota na
cédula e vê o voto do apartamento; o placar só aparece no fim."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_sindico_convoca_e_morador_vota(navegador):
    titulo = f"Assembleia de teste {random.randint(1000, 9999)}"
    ctx, pg = abrir(navegador, papel="sindico")
    sindico = token_da_aba(pg)
    try:
        ir(pg, "pages/sindico/assembleias.html", 1500)
        pg.fill("#aTitulo", titulo)
        # Abre já: o minuto atual, no relógio da tela.
        pg.evaluate("""() => {
            const d = new Date(), dd = n => ('0' + n).slice(-2);
            document.getElementById('aAbre').value = d.getFullYear() + '-' + dd(d.getMonth() + 1) +
              '-' + dd(d.getDate()) + 'T' + dd(d.getHours()) + ':' + dd(d.getMinutes());
        }""")
        pg.fill("#itensPauta .item-titulo >> nth=0", "Reforma do parquinho")
        pg.click("#btnNovoItem")
        pg.fill("#itensPauta .item-titulo >> nth=1", "Mudar o regimento interno")
        pg.select_option("#itensPauta .item-maioria >> nth=1", "dois_tercos")
        pg.click("#formAssembleia button[type=submit]")
        pg.wait_for_selector("#erroAssembleia.sucesso", timeout=8000)
        cartao = pg.locator("#listaAssembleias .assembleia", has_text=titulo)
        cartao.wait_for(timeout=8000)
        texto = cartao.inner_text()
        assert "Votação aberta" in texto and "2/3 dos apartamentos" in texto, texto
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/assembleias.html", 1500)
        cartao = pg.locator("#listaAssembleias .assembleia", has_text=titulo)
        cartao.wait_for(timeout=8000)
        # Sem marcar todos os itens, a cédula não sai.
        cartao.locator(".opcoes-voto >> nth=0").get_by_label("A favor").check()
        cartao.get_by_role("button", name="Confirmar o voto do apartamento").click()
        cartao.get_by_text("Escolha uma opção em cada item").wait_for(timeout=4000)
        cartao.locator(".opcoes-voto >> nth=1").get_by_label("Contra").check()
        pg.once("dialog", lambda d: d.accept())
        cartao.get_by_role("button", name="Confirmar o voto do apartamento").click()
        pg.locator("#listaAssembleias .assembleia", has_text=titulo).get_by_text(
            "Voto do seu apartamento: Contra").wait_for(timeout=8000)
        cartao = pg.locator("#listaAssembleias .assembleia", has_text=titulo)
        assert "Seu apartamento já votou." in cartao.inner_text()
        assert cartao.locator(".cedula").count() == 0
        # O placar continua escondido enquanto a votação está aberta.
        assert "Aprovado" not in cartao.inner_text()
        assert pg.erros == []
    finally:
        for a in pg.request.get(f"{API}/assembleias", headers=sindico).json():
            if a["titulo"] == titulo and a["situacao"] in ("agendada", "aberta"):
                pg.request.post(f"{API}/assembleias/{a['id']}/cancelamento", headers=sindico,
                                data={"motivo": "Limpeza do teste"})
        ctx.close()
