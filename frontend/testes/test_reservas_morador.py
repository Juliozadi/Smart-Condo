"""Próximas reservas do morador: as mais perto de hoje primeiro.

A API manda da mais recente para a mais antiga, e o painel pegava as três
primeiras: "próximas" mostrava as mais distantes.
"""
from __future__ import annotations

from datetime import date, timedelta

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_painel_mostra_primeiro_a_reserva_mais_proxima(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "morador@smartcondo.com", "senha": "smartcondo123"})
    cab = {"Authorization": "Bearer " + r.json()["access_token"]}
    espaco = next(e for e in pg.request.get(f"{API}/espacos", headers=cab).json()
                  if e["nome"] == "Churrasqueira 1")
    criadas = []
    for dias in (40, 25):
        resp = pg.request.post(f"{API}/espacos/reservas", headers=cab, data={
            "espaco_id": espaco["id"], "data": (date.today() + timedelta(days=dias)).isoformat(),
            "hora_inicio": "10:00", "hora_fim": "12:00", "pessoas_estimadas": 5})
        assert resp.ok, resp.text()
        criadas.append(resp.json()["id"])
    try:
        minhas = pg.request.get(f"{API}/espacos/reservas/minhas", headers=cab).json()
        abertas = sorted((m["data"] for m in minhas if m["status"] in ("pendente", "aprovada")))
        ir(pg, "pages/morador/dashboard.html", 1500)
        primeiro = pg.locator("#listaReservas .reserve-card").first.inner_text()
        dia = abertas[0][8:10]
        assert primeiro.startswith(dia), (primeiro, abertas)
        assert pg.erros == []
    finally:
        for rid in criadas:
            pg.request.delete(f"{API}/espacos/reservas/{rid}", headers=cab)
        ctx.close()
