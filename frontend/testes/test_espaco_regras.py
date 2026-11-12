"""Regras de uso do espaço: o síndico define, o morador vê antes de pedir.

O salão até as 22h, a churrasqueira por no máximo seis horas, uma reserva
futura por apartamento: nada disso existia, e qualquer horário passava.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_sindico_define_as_regras_e_morador_as_ve_e_respeita(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/reservas.html", 1500)
    nome = f"Quadra {random.randint(1000, 9999)}"

    pg.click("#btnNovoEspaco")
    pg.fill("#eNome", nome)
    pg.fill("#eAbre", "08:00")
    pg.fill("#eFecha", "20:00")
    pg.fill("#eDuracao", "2")
    pg.fill("#eLimite", "1")
    pg.click("#btnSalvar")
    cartao = pg.locator("#listaEspacos .list-item", has_text=nome)
    cartao.wait_for(timeout=8000)
    texto = cartao.inner_text()
    assert "das 08h00 às 20h00" in texto and "até 2h por reserva" in texto, texto
    assert pg.erros == []

    # Para espaço de uso livre (piscina), as regras somem do formulário.
    pg.click("#btnNovoEspaco")
    pg.select_option("#eTipo", "uso_livre")
    assert pg.locator("#regrasEspaco").is_hidden()
    pg.click("#btnCancelar")

    sindico = {"Authorization": "Bearer " + pg.request.post(
        f"{API}/auth/login", data={"email": "sindico@smartcondo.com",
                                   "senha": "smartcondo123"}).json()["access_token"]}
    espaco = next(e for e in pg.request.get(f"{API}/espacos", headers=sindico).json()
                  if e["nome"] == nome)
    ctx.close()

    try:
        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/reservas.html", 1500)
        pg.select_option("#reserv_espacoDesejado", label=nome)
        regras = pg.inner_text("#regrasEspaco")
        assert "funciona das 08h00 às 20h00" in regras and "1 reserva futura por apartamento" in regras

        pg.fill("#reserv_data", (date.today() + timedelta(days=10)).isoformat())
        pg.fill("#reserv_horarioDeInicio", "19:00")
        pg.fill("#reserv_horarioDeTermino", "21:00")
        pg.click("#formReserva button[type=submit]")
        pg.locator("#erroReserva", has_text="funciona das 08:00 às 20:00").wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        pg.request.delete(f"{API}/espacos/{espaco['id']}", headers=sindico)
        ctx.close()
