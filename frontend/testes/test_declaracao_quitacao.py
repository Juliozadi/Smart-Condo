"""Declaração de quitação: a Ana emite a do 301 e abre a página pública;
o síndico não consegue a do 302, que está em atraso, e revoga a da Ana;
quem confere o código vê que ela não vale mais."""
from __future__ import annotations

from conftest import FRONT, SENHA, abrir, ir


def entrar_como(navegador, email, largura=420):
    ctx = navegador.new_context(viewport={"width": largura, "height": 850},
                                timezone_id="America/Campo_Grande")
    pg = ctx.new_page()
    pg.erros = []
    pg.on("pageerror", lambda e: pg.erros.append(str(e)))
    pg.goto(f"{FRONT}/index.html")
    pg.fill("#emailInput", email)
    pg.fill("#senhaInput", SENHA)
    pg.click("#btnEntrar")
    pg.wait_for_url("**/morador/dashboard.html", timeout=15000)
    return ctx, pg


def test_emitir_conferir_e_revogar(navegador):
    ctx, pg = entrar_como(navegador, "ana@smartcondo.com")
    try:
        ir(pg, "pages/morador/financeiro.html", 1200)
        pg.get_by_role("link", name="Declaração de quitação").click()
        pg.wait_for_url("**/morador/quitacao.html")
        pg.click("#btnEmitir")
        pg.wait_for_selector("#erroEmitir.sucesso", timeout=8000)
        cartao = pg.locator("#listaDeclaracoes .declaracao", has_text="Válida").first
        codigo = cartao.locator(".declaracao-codigo strong").inner_text()
        with ctx.expect_page() as aba:
            cartao.get_by_role("link", name=f"Abrir a declaração {codigo}").click()
        publica = aba.value
        publica.wait_for_selector("#resultado:not([hidden])", timeout=8000)
        assert "apartamento 301 não possui débitos" in publica.inner_text("#docTexto")
        assert "válida" in publica.inner_text("#docSituacao")
        assert pg.erros == []
        ctx.close()

        ctx, pg = abrir(navegador, papel="sindico")
        ir(pg, "pages/sindico/quitacao.html", 1500)
        # O 302 está em atraso: a API recusa e diz quanto falta.
        pg.select_option("#dUnidade", label="Apto 302")
        pg.click("#formDeclaracao button[type=submit]")
        pg.wait_for_selector("#erroDeclaracao:has-text('vencida')", timeout=8000)

        cartao = pg.locator(".declaracao", has_text=codigo)
        pg.once("dialog", lambda d: d.accept("O pagamento de outubro foi estornado pelo banco."))
        cartao.get_by_role("button", name=f"Revogar a declaração {codigo} do apto 301").click()
        pg.locator(".declaracao", has_text=codigo).get_by_text("Revogada", exact=True) \
            .wait_for(timeout=8000)
        assert pg.erros == []
        ctx.close()

        # Sem login, quem recebeu o código vê que ela não vale mais.
        ctx, pg = abrir(navegador, largura=420)
        ir(pg, "pages/verificar/declaracao.html", 800)
        pg.fill("#vCodigo", codigo.replace("-", "").lower())
        pg.click("#btnVerificar")
        pg.wait_for_selector("#docSituacao.revogada", timeout=8000)
        assert "estornado" not in pg.inner_text("body")
        pg.fill("#vCodigo", "AAAA-BBBB-CCCC-DDDD")
        pg.click("#btnVerificar")
        pg.wait_for_selector("#erroVerificar:has-text('não encontrada')", timeout=8000)
        assert pg.is_hidden("#resultado")
        assert pg.erros == []
    finally:
        ctx.close()
