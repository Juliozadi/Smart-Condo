"""Visitante autorizado com antecedência pelo morador.

O morador libera a diarista pela tela; a portaria a vê em "Autorizados
para hoje", digita o CPF do documento apresentado e registra a entrada
sem esperar resposta. CPF diferente do autorizado não passa.
"""
from __future__ import annotations

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from conftest import FRONT, abrir, ir
from test_arquivos import cpf_valido

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def _token(pg, email):
    r = pg.request.post(f"{API}/auth/login", data={"email": email, "senha": "smartcondo123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def _cpf_diferente(cpf):
    outro = cpf_valido()
    while outro == cpf:
        outro = cpf_valido()
    return outro


def test_morador_autoriza_e_portaria_registra_a_entrada(navegador):
    nome = f"Diarista Teste {random.randint(1000, 9999)}"
    cpf = cpf_valido()
    ctx, pg = abrir(navegador, papel="morador")
    morador = _token(pg, "morador@smartcondo.com")
    porteiro = _token(pg, "porteiro@smartcondo.com")
    try:
        ir(pg, "pages/morador/visitantes.html", 1200)
        pg.fill("#aut_nome", nome)
        pg.select_option("#aut_tipo", "Diarista")
        pg.fill("#aut_documento", cpf)
        # Só no dia da semana de hoje (no fuso do condomínio): continua valendo hoje.
        dia = datetime.now(ZoneInfo("America/Campo_Grande")).isoweekday()
        pg.check(f"input[name=aut_dia][value='{dia}']")
        pg.click("#formAutorizacao button[type=submit]")
        pg.wait_for_selector("#erroAutorizacao.sucesso", timeout=8000)
        cartao = pg.locator("#listaAutorizacoes .list-item", has_text=nome)
        cartao.wait_for(timeout=8000)
        assert "Vale hoje" in cartao.inner_text()
        sigla = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"][dia - 1]
        assert f"· {sigla} ·" in cartao.inner_text()
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="porteiro")
        ir(pg, "pages/porteiro/visitantes.html", 1500)
        autorizado = pg.locator("#listaAutorizados .list-item", has_text=nome)
        autorizado.wait_for(timeout=8000)
        # A portaria não vê o CPF inteiro: precisa digitar o do documento.
        assert cpf not in autorizado.inner_text()
        autorizado.locator("button", has_text="Registrar entrada").click()
        assert pg.input_value("#nome-visitante") == nome
        assert pg.locator("#avisoAutorizacao").is_visible()

        pg.fill("#doc-visitante", _cpf_diferente(cpf))
        pg.click("#formVisitante button[type=submit]")
        pg.locator("#erroVisitante", has_text="não confere").wait_for(timeout=8000)

        pg.fill("#doc-visitante", cpf)
        pg.click("#formVisitante button[type=submit]")
        pg.wait_for_selector("#erroVisitante.sucesso", timeout=8000)
        assert "autorização do morador" in pg.inner_text("#erroVisitante")
        assert pg.locator("#avisoAutorizacao").is_hidden()
        pg.locator("#listaPresentes .list-item", has_text=nome).get_by_text("Dentro").wait_for(
            timeout=8000)
        autorizado.get_by_text("Dentro").wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        for v in pg.request.get(f"{API}/portaria/visitantes?status=dentro", headers=porteiro).json():
            if v["nome"] == nome:
                pg.request.post(f"{API}/portaria/visitantes/{v['id']}/saida", headers=porteiro)
        for a in pg.request.get(f"{API}/portaria/autorizacoes", headers=morador).json():
            if a["nome"] == nome:
                pg.request.delete(f"{API}/portaria/autorizacoes/{a['id']}", headers=morador)
        ctx.close()
