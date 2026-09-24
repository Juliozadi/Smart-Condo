"""Trocar a senha encerra as sessões abertas em outros aparelhos.

Quem troca a senha porque desconfia que alguém entrou na conta espera que
esse alguém saia. A aba em que a senha foi trocada continua conectada.
"""
from __future__ import annotations

from conftest import SENHA, abrir, ir

NOVA = "outrasenha123"


def test_trocar_a_senha_derruba_o_outro_aparelho(navegador):
    outro_ctx, outro = abrir(navegador, papel="morador")   # o "outro aparelho"
    ctx, pg = abrir(navegador, papel="morador")
    try:
        ir(pg, "pages/morador/perfil.html", 1000)
        pg.fill("#senhaAtual", SENHA)
        pg.fill("#senhaNova", NOVA)
        pg.fill("#senhaConfirma", NOVA)
        pg.click("#formSenha button[type=submit]")
        pg.wait_for_selector("#erroSenha.sucesso", timeout=10000)
        assert "outros aparelhos" in pg.inner_text("#erroSenha")

        # Esta aba segue conectada, com o token novo.
        ir(pg, "pages/morador/comunicados.html", 1000)
        assert "comunicados.html" in pg.url

        # O outro aparelho cai no login na próxima ação.
        outro.goto(outro.url)
        outro.wait_for_url("**/index.html?sessao=*", timeout=10000)
        assert pg.erros == [] and outro.erros == []
    finally:
        # Devolve a senha de sempre, que os outros testes usam.
        pg.evaluate("""([atual, nova]) => window.SmartCondo.api.post('/auth/senha/trocar',
            {senha_atual: atual, nova_senha: nova}).catch(() => null)""", [NOVA, SENHA])
        ctx.close()
        outro_ctx.close()
