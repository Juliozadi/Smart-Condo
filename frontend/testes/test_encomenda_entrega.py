"""O porteiro entrega a encomenda em mãos e dá baixa pela tela."""
from __future__ import annotations

import random

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def test_porteiro_entrega_em_maos(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "porteiro@smartcondo.com", "senha": "smartcondo123"})
    cab = {"Authorization": "Bearer " + r.json()["access_token"]}
    unidade = pg.request.get(f"{API}/condominios/meu/unidades", headers=cab).json()[0]
    remetente = f"Loja {random.randint(1000, 9999)}"
    assert pg.request.post(f"{API}/portaria/encomendas", headers=cab, data={
        "unidade_id": unidade["id"], "remetente": remetente, "tipo_volume": "Envelope"}).ok
    ir(pg, "pages/porteiro/encomendas.html", 1500)
    cartao = pg.locator("#listaAguardando .list-item", has_text=remetente)
    pg.once("dialog", lambda d: d.accept("Maria (vizinha)"))
    cartao.get_by_role("button", name="Entregar").click()
    pg.wait_for_timeout(1200)
    assert pg.locator("#listaAguardando .list-item", has_text=remetente).count() == 0
    lista = pg.request.get(f"{API}/portaria/encomendas", headers=cab).json()
    feita = next(e for e in lista if e["remetente"] == remetente)
    assert feita["status"] == "retirada" and feita["retirado_por_nome"] == "Maria (vizinha)"
    assert pg.erros == []
    ctx.close()
