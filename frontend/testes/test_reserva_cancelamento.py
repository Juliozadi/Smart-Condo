"""O síndico cancela uma reserva aprovada, e o morador vê o motivo.

Antes, o síndico só avaliava as pendentes; e o morador nunca via o motivo
de uma recusa, porque a recusada ia direto para o histórico, que não o
mostrava.
"""
from __future__ import annotations

from datetime import date, timedelta

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def _token(pg, email):
    r = pg.request.post(f"{API}/auth/login", data={"email": email, "senha": "smartcondo123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_sindico_cancela_pela_tela_e_morador_ve_o_motivo(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    morador = _token(pg, "morador@smartcondo.com")
    sindico = token_da_aba(pg)
    espaco = next(e for e in pg.request.get(f"{API}/espacos", headers=morador).json()
                  if e["nome"] == "Churrasqueira 1")
    dia = date.today() + timedelta(days=55)
    criada = pg.request.post(f"{API}/espacos/reservas", headers=morador, data={
        "espaco_id": espaco["id"], "data": dia.isoformat(),
        "hora_inicio": "07:00", "hora_fim": "08:00", "pessoas_estimadas": 4})
    assert criada.ok, criada.text()
    reserva = criada.json()
    aprovada = pg.request.post(f"{API}/espacos/reservas/{reserva['id']}/avaliacao",
                               headers=sindico, data={"aprovada": True})
    assert aprovada.ok, aprovada.text()

    try:
        ir(pg, "pages/sindico/reservas.html", 1500)
        rotulo = dia.strftime("%d/%m") + " · 07h00–08h00"
        linha = pg.locator("#tabelaReservas .table-row", has_text=rotulo)
        pg.once("dialog", lambda d: d.accept("Obra na churrasqueira"))
        linha.get_by_role("button", name="Cancelar").click()
        linha.get_by_text("Cancelada").wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="morador")
        ir(pg, "pages/morador/reservas.html", 1500)
        cartao = pg.locator("#minhasReservas", has_text="Cancelada pelo síndico: Obra na churrasqueira")
        cartao.wait_for(timeout=8000)
        assert pg.erros == []
    finally:
        # Se o teste parou antes de cancelar, a reserva não fica ocupando o horário.
        pg.request.post(f"{API}/espacos/reservas/{reserva['id']}/cancelamento",
                        headers=sindico, data={"motivo": "Limpeza do teste"})
        ctx.close()
