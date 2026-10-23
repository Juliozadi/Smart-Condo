"""Uma pessoa, vários perfis: o síndico que também mora troca de perfil no
topo da tela; o dono de um apartamento alugado vê só o que é do dono; e
o perfil acrescenta (e tira) apartamentos."""
from __future__ import annotations

from conftest import FRONT, abrir, ir, token_da_aba

API = FRONT.rsplit(":", 1)[0] + ":8000/api/v1"


def trocar_para(pg, texto):
    pg.click(".perfil-trocar")
    pg.locator(".perfil-menu-item", has_text=texto).click()


def test_sindico_que_mora_troca_de_perfil(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    try:
        trocar_para(pg, "Apto 101")
        pg.wait_for_url("**/morador/dashboard.html", timeout=8000)
        pg.locator("#saudacaoCondominio", has_text="Apto 101").wait_for(timeout=8000)
        assert pg.locator(".profile-role").first.inner_text() == "Morador"
        # De volta ao síndico, sem digitar a senha.
        trocar_para(pg, "Síndico")
        pg.wait_for_url("**/sindico/dashboard.html", timeout=8000)
        assert pg.erros == []
    finally:
        ctx.close()


def test_dono_do_apartamento_alugado(navegador):
    ctx, pg = abrir(navegador, largura=420, papel="morador")
    try:
        trocar_para(pg, "302")
        pg.wait_for_url("**/morador/dashboard.html", timeout=8000)
        pg.locator("#avisoNaoReside").wait_for(state="visible", timeout=8000)
        # A portaria do apartamento é de quem mora lá.
        assert not pg.locator("a.dash-card[href='visitantes.html']").is_visible()
        assert not pg.locator("a.dash-card[href='reservas.html']").is_visible()
        assert pg.locator("a.dash-card[href='financeiro.html']").is_visible()
        assert pg.erros == []
    finally:
        ctx.close()


def test_acrescentar_e_tirar_apartamento(navegador):
    ctx, pg = abrir(navegador, papel="morador")
    tok = token_da_aba(pg)
    try:
        ir(pg, "pages/morador/perfil.html", 1500)
        caixa = pg.locator("#meusApartamentos")
        caixa.locator(".apto-item", has_text="Apto 302").wait_for(timeout=8000)
        pg.select_option("#aptoUnidade", label="Apto 410")
        pg.uncheck("#aptoReside")
        caixa.get_by_role("button", name="Acrescentar apartamento").click()
        pg.wait_for_selector("#erroApto.sucesso", timeout=8000)
        item = caixa.locator(".apto-item", has_text="Apto 410")
        assert "aguardando o síndico" in item.inner_text()
        pg.once("dialog", lambda d: d.accept())
        item.get_by_role("button", name="Tirar o apartamento 410 do cadastro").click()
        caixa.locator(".apto-item", has_text="Apto 410").wait_for(state="detached", timeout=8000)
        assert pg.erros == []
    finally:
        for p in pg.request.get(f"{API}/auth/perfis", headers=tok).json():
            if p["unidade"] == "410":
                pg.request.delete(f"{API}/usuarios/eu/apartamentos/{p['usuario_id']}", headers=tok)
        ctx.close()
