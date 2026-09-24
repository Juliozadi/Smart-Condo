"""Acessibilidade medida pelo axe-core (WCAG 2.1 A e AA e boas práticas).

A auditoria encontrou, e estes testes impedem que volte: o botão de
acessibilidade com um atributo proibido (o nome dele podia não ser
anunciado), a tabela de visitantes com linhas sem tabela nem células, o
link "voltar" e o do perfil sem texto no celular, páginas sem título
principal e títulos que pulavam níveis. O contraste de cores fica de fora:
é medido por ferramentas/contraste.js, que sabe lidar com os degradês.
"""
from __future__ import annotations

from pathlib import Path

import axe_playwright_python
import pytest

from conftest import PAPEIS, PUBLICAS, abrir, ir, paginas_do_papel

AXE = (Path(axe_playwright_python.__file__).parent / "axe.min.js").read_text(encoding="utf-8")
REGRAS = """async () => (await axe.run(document, {
    runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']},
    rules: {'color-contrast': {enabled: false}}
  })).violations.map(v => v.id + ' (' + v.impact + '): ' +
     v.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | '))"""


def auditar(pg, pagina):
    pg.add_script_tag(content=AXE)
    return [f"{pagina}: {v}" for v in pg.evaluate(REGRAS)]


@pytest.mark.parametrize("largura", (1280, 390))
@pytest.mark.parametrize("papel", (None,) + PAPEIS)
def test_telas_sem_violacoes(navegador, papel, largura):
    ctx, pg = abrir(navegador, largura, "light", papel)
    paginas = PUBLICAS if papel is None else paginas_do_papel(papel)
    problemas = []
    for pagina in paginas:
        ir(pg, pagina, 900)
        problemas += auditar(pg, pagina)
    ctx.close()
    assert not problemas, "\n".join(problemas)


def test_menu_de_acessibilidade_aberto(navegador):
    ctx, pg = abrir(navegador)
    ir(pg, "index.html", 600)
    pg.click("label.access-button")
    pg.wait_for_timeout(300)
    problemas = auditar(pg, "index.html com o menu aberto")
    ctx.close()
    assert not problemas, "\n".join(problemas)


def test_chat_aberto(navegador):
    ctx, pg = abrir(navegador, papel="sindico")
    pg.wait_for_timeout(800)
    pg.click(".chat-abrir")
    pg.wait_for_timeout(800)
    problemas = auditar(pg, "chat aberto")
    ctx.close()
    assert not problemas, "\n".join(problemas)


@pytest.mark.parametrize("papel", (None, "morador"))
def test_menu_de_acessibilidade_pelo_teclado(navegador, papel):
    """O menu era inalcançável pelo teclado: a caixa que o abre estava com
    display:none, e o Tab passava direto. Justo a ferramenta de quem mais
    depende do teclado."""
    ctx, pg = abrir(navegador, papel=papel)
    ir(pg, "index.html" if papel is None else "pages/morador/dashboard.html", 800)
    for _ in range(60):
        pg.keyboard.press("Tab")
        if pg.evaluate("document.activeElement.id") == "access-toggle":
            break
    else:
        pytest.fail("o Tab não chega ao botão de acessibilidade")
    pg.keyboard.press("Enter")
    assert pg.is_visible(".access-menu")
    pg.keyboard.press("Tab")
    assert pg.evaluate("document.activeElement.id") == "font-toggle"
    pg.keyboard.press("Space")
    assert pg.is_checked("#font-toggle")
    pg.keyboard.press("Space")      # desfaz, para não mudar as outras telas
    pg.keyboard.press("Escape")
    assert not pg.is_visible(".access-menu")
    assert pg.evaluate("document.activeElement.id") == "access-toggle"
    assert pg.erros == []
    ctx.close()
