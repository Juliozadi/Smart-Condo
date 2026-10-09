"""Painel do porteiro com permissões limitadas.

O síndico bloqueava "visitantes" e "encomendas", e o painel continuava
mostrando os contadores ("—") e as seções com o aviso de que a ação não
foi liberada. Agora o que não foi liberado some do painel.
"""
from __future__ import annotations

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"
TODAS = {"registrar_visitantes": True, "registrar_encomendas": True,
         "registrar_veiculos": True, "registrar_ocorrencias": True}


def test_painel_mostra_so_o_que_foi_liberado(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    r = pg.request.post(f"{API}/auth/login",
                        data={"email": "sindico@smartcondo.com", "senha": "smartcondo123"})
    cab = {"Authorization": "Bearer " + r.json()["access_token"]}
    carlos = next(u for u in pg.request.get(f"{API}/usuarios?papel=porteiro", headers=cab).json()
                  if u["email"] == "porteiro@smartcondo.com")
    url = f"{API}/usuarios/porteiros/{carlos['id']}/permissoes"
    pg.request.put(url, headers=cab, data={**TODAS, "registrar_visitantes": False,
                                           "registrar_encomendas": False})
    try:
        ir(pg, "pages/porteiro/dashboard.html", 1800)
        texto = pg.inner_text("main").lower()
        assert "visitantes no condomínio agora" not in texto
        assert "encomendas aguardando retirada" not in texto
        assert "não liberou" not in texto
        assert pg.is_visible("#totVeiculos") and not pg.is_visible("#totVisitantes")
        assert pg.erros == []
    finally:
        pg.request.put(url, headers=cab, data=TODAS)
        ctx.close()


def test_com_tudo_liberado_mostra_tudo(navegador):
    ctx, pg = abrir(navegador, papel="porteiro")
    ir(pg, "pages/porteiro/dashboard.html", 1800)
    texto = pg.inner_text("main").lower()
    assert "visitantes no condomínio agora" in texto and "encomendas aguardando retirada" in texto
    assert pg.is_visible("#totVisitantes") and pg.is_visible("#totEncomendas")
    ctx.close()
