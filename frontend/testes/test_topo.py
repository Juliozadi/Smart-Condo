"""A marca no topo não fica por baixo dos botões.

No painel do síndico, num monitor de 1440px, "SmartCondo" aparecia
cortado: a barra dos painéis tem 480px em qualquer tela, e o botão
"Mensagens" por extenso, o nome e o "Sair" não deixavam lugar para ela.
"""
from __future__ import annotations

import pytest

from conftest import abrir, ir, paginas_do_papel

SOBREPOSICAO = """() => {
  const nome = document.querySelector('.brand-name').getBoundingClientRect();
  const direita = document.querySelector('.app-bar-right').getBoundingClientRect();
  return {marca_termina: nome.right, botoes_comecam: direita.left};
}"""


@pytest.mark.parametrize("largura", (1440, 390))
@pytest.mark.parametrize("papel", ("sindico", "morador", "porteiro", "admin"))
def test_marca_e_botoes_nao_se_sobrepoem(navegador, papel, largura):
    ctx, pg = abrir(navegador, largura=largura, papel=papel)
    try:
        for pagina in paginas_do_papel(papel):
            ir(pg, pagina, 500)
            pg.wait_for_selector(".chat-abrir", timeout=5000) if papel != "admin" else None
            medida = pg.evaluate(SOBREPOSICAO)
            assert medida["marca_termina"] <= medida["botoes_comecam"] + 0.5, (pagina, medida)
    finally:
        ctx.close()
