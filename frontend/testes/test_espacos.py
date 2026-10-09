"""Espaços comuns: o síndico cadastra, edita, inativa e reativa pela tela.

Antes não havia tela para isso: só a carga de demonstração criava
espaços, e um condomínio novo ficava sem nada para reservar.
"""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def nomes_para_o_morador(pg):
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "ana@smartcondo.com", "senha": "smartcondo123"})
    cab = {"Authorization": "Bearer " + r.json()["access_token"]}
    return [e["nome"] for e in pg.request.get(f"{API}/espacos", headers=cab).json()]


def test_sindico_cadastra_edita_inativa_e_reativa_um_espaco(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/reservas.html", 1500)
    nome = f"Quadra {random.randint(1000, 9999)}"

    pg.click("#btnNovoEspaco")
    pg.fill("#eNome", nome)
    pg.fill("#eCapacidade", "30")
    pg.fill("#eDescricao", "Poliesportiva")
    pg.click("#btnSalvar")
    cartao = pg.locator("#listaEspacos .list-item", has_text=nome)
    cartao.wait_for(timeout=8000)
    assert "Reservável · até 30 pessoas · Poliesportiva" in cartao.inner_text()
    assert "Criado por Roberto Nascimento em" in cartao.inner_text()
    assert nome in nomes_para_o_morador(pg)

    # Edição: a janela vem preenchida e a linha mostra quem editou.
    cartao.get_by_role("button", name=f"Editar {nome}").click()
    assert pg.input_value("#eCapacidade") == "30"
    pg.fill("#eCapacidade", "40")
    pg.check("#eManutencao")
    pg.click("#btnSalvar")
    pg.wait_for_timeout(1200)
    cartao = pg.locator("#listaEspacos .list-item", has_text=nome)
    texto = cartao.inner_text()
    assert "Em manutenção" in texto and "até 40 pessoas" in texto
    assert "Editado por Roberto Nascimento em" in texto

    # Inativar: some para o morador; nada é apagado e dá para reativar.
    pg.once("dialog", lambda d: d.accept())
    cartao.get_by_role("button", name=f"Inativar {nome}").click()
    pg.wait_for_timeout(1200)
    cartao = pg.locator("#listaEspacos .list-item", has_text=nome)
    assert "Inativo" in cartao.inner_text()
    assert nome not in nomes_para_o_morador(pg)
    pg.once("dialog", lambda d: d.accept())
    cartao.get_by_role("button", name=f"Reativar {nome}").click()
    pg.wait_for_timeout(1200)
    cartao = pg.locator("#listaEspacos .list-item", has_text=nome)
    assert "Reativado por Roberto Nascimento" in cartao.inner_text()
    assert nome in nomes_para_o_morador(pg)
    assert pg.erros == []
    ctx.close()


def test_nome_vazio_nao_envia(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/reservas.html", 1200)
    antes = pg.locator("#listaEspacos .list-item").count()
    pg.click("#btnNovoEspaco")
    pg.click("#btnSalvar")
    assert pg.inner_text("#modalErro") == "Informe o nome do espaço."
    pg.keyboard.press("Escape")
    assert pg.locator("#listaEspacos .list-item").count() == antes
    ctx.close()
