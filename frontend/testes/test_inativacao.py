"""O síndico tira o acesso de quem saiu do condomínio.

Não havia botão para isso: a API tinha a rota, mas nenhuma tela a usava.
O morador que se mudava e o porteiro que deixava a equipe continuavam
entrando e vendo o condomínio. Estes testes usam contas da carga de
demonstração que nenhum outro teste usa (Bruno e Renata).
"""
from __future__ import annotations

from conftest import FRONT, abrir, ir

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def entrar(pg, email):
    r = pg.request.post(f"{API}/auth/login", data={"email": email, "senha": "smartcondo123"})
    return r


def test_sindico_inativa_um_morador(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    tok_bruno = entrar(pg, "bruno@smartcondo.com").json()["access_token"]
    ir(pg, "pages/sindico/moradores.html", 1200)
    linha = pg.locator("#tabelaMoradores .table-row", has_text="Bruno Cardoso")
    avisos = []
    pg.once("dialog", lambda d: (avisos.append(d.message), d.accept()))
    linha.get_by_role("button", name="Inativar Bruno Cardoso").click()
    pg.wait_for_timeout(1200)
    assert "reservas futuras são canceladas" in avisos[0]
    linha = pg.locator("#tabelaMoradores .table-row", has_text="Bruno Cardoso")
    assert "Inativo" in linha.inner_text()
    assert linha.get_by_role("button").count() == 0
    # O acesso acabou na hora, inclusive a sessão que já estava aberta.
    r = pg.request.get(f"{API}/auth/eu", headers={"Authorization": f"Bearer {tok_bruno}"})
    assert r.status == 403
    assert entrar(pg, "bruno@smartcondo.com").status == 403
    assert pg.erros == []
    ctx.close()


def test_sindico_inativa_um_porteiro(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/porteiros.html", 1200)
    pg.once("dialog", lambda d: d.accept())
    pg.get_by_role("button", name="Inativar Renata Moura").click()
    pg.wait_for_timeout(1200)
    assert pg.get_by_role("button", name="Inativar Renata Moura").count() == 0
    assert entrar(pg, "renata@smartcondo.com").status == 403
    assert pg.erros == []
    ctx.close()


def test_cancelar_a_confirmacao_nao_inativa(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    ir(pg, "pages/sindico/moradores.html", 1200)
    pg.once("dialog", lambda d: d.dismiss())
    pg.get_by_role("button", name="Inativar Ana Beatriz Rocha").click()
    pg.wait_for_timeout(600)
    assert entrar(pg, "ana@smartcondo.com").status == 200
    ctx.close()
