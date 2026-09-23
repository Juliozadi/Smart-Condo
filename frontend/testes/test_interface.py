"""Testes de interface: o que já quebrou uma vez e não pode voltar.

Cada teste corresponde a um defeito real encontrado nas telas:

- a barra superior descia do topo nas telas mais curtas que a janela;
- grupos de itens iguais em que metade tinha ícone e metade não, porque
  ícones tinham sido removidos e deixado o espaço vazio;
- caixas com cor clara escrita à mão que continuavam claras no tema
  escuro, e o brilho de hover que ficava parado sobre o item;
- telas com erro de JavaScript, imagem quebrada ou rolagem lateral no
  celular;
- elementos marcados como escondidos (hidden) que apareciam mesmo assim,
  porque uma regra de display do CSS anulava o atributo — o contador de
  mensagens mostrava "0" e o aviso da câmera ficava ao lado da foto;
- a logo das telas internas levava à tela de entrada, e não ao painel.
"""
from __future__ import annotations

import pytest

from conftest import PAPEIS, PUBLICAS, abrir, ir, paginas_do_papel

LARGURAS = (1280, 390)
TEMAS = ("light", "dark")


def _todas(papel):
    return paginas_do_papel(papel)


# ── Erros de JavaScript, imagens e rolagem lateral ────────────────────
CHECA_TELA = """() => ({
  rolagemLateral: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  quebradas: [...document.images]
     .filter(i => i.getAttribute('src') && i.complete && i.naturalWidth === 0 && !/vlibras/.test(i.src))
     .map(i => i.getAttribute('src')),
  escondidosVisiveis: [...document.querySelectorAll('[hidden]')]
     .filter(e => getComputedStyle(e).display !== 'none')
     .map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + '.' + e.className)
})"""


@pytest.mark.parametrize("largura", LARGURAS)
@pytest.mark.parametrize("tema", TEMAS)
def test_telas_publicas_sem_erro(navegador, largura, tema):
    ctx, pg = abrir(navegador, largura, tema)
    problemas = []
    for pagina in PUBLICAS:
        pg.erros.clear()
        ir(pg, pagina, 400)
        r = pg.evaluate(CHECA_TELA)
        if pg.erros: problemas.append(f"{pagina}: erro de JavaScript {pg.erros}")
        if r["rolagemLateral"]: problemas.append(f"{pagina}: rolagem lateral")
        if r["quebradas"]: problemas.append(f"{pagina}: imagem quebrada {r['quebradas']}")
        if r["escondidosVisiveis"]:
            problemas.append(f"{pagina}: escondido aparecendo {r['escondidosVisiveis']}")
    ctx.close()
    assert not problemas, "\n".join(problemas)


@pytest.mark.parametrize("papel", PAPEIS)
@pytest.mark.parametrize("largura", LARGURAS)
@pytest.mark.parametrize("tema", TEMAS)
def test_telas_internas_sem_erro(navegador, papel, largura, tema):
    ctx, pg = abrir(navegador, largura, tema, papel)
    problemas = []
    for pagina in _todas(papel):
        pg.erros.clear()
        ir(pg, pagina)
        r = pg.evaluate(CHECA_TELA)
        if pg.erros: problemas.append(f"{pagina}: erro de JavaScript {pg.erros}")
        if r["rolagemLateral"]: problemas.append(f"{pagina}: rolagem lateral")
        if r["quebradas"]: problemas.append(f"{pagina}: imagem quebrada {r['quebradas']}")
        if r["escondidosVisiveis"]:
            problemas.append(f"{pagina}: escondido aparecendo {r['escondidosVisiveis']}")
    ctx.close()
    assert not problemas, "\n".join(problemas)


# ── Barra superior presa no topo ──────────────────────────────────────
@pytest.mark.parametrize("papel", PAPEIS)
@pytest.mark.parametrize("altura", (1400, 700))
def test_barra_superior_fica_no_topo(navegador, papel, altura):
    """Sem rolar e rolado até o fim, a barra tem de estar em y = 0."""
    ctx, pg = abrir(navegador, 1280, "light", papel)
    pg.set_viewport_size({"width": 1280, "height": altura})
    fora = []
    for pagina in _todas(papel):
        ir(pg, pagina)
        topo = pg.evaluate("document.querySelector('.app-bar').getBoundingClientRect().top")
        pg.evaluate("scrollTo(0, 99999)")
        rolado = pg.evaluate("document.querySelector('.app-bar').getBoundingClientRect().top")
        if round(topo) != 0 or round(rolado) != 0:
            fora.append(f"{pagina}: topo={topo:.0f} rolado={rolado:.0f}")
    ctx.close()
    assert not fora, "\n".join(fora)


# ── Ícones: itens iguais, tratamento igual ────────────────────────────
ICONES_FALTANDO = """() => {
  const tem = e => !!e.querySelector('img,svg');
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const out = [];
  // Títulos de seção, banners e cartões de números: sempre com ícone.
  for (const sel of ['.section-title', '.greeting-name', '.stat-label']) {
    document.querySelectorAll(sel).forEach(e => {
      if (vis(e) && !tem(e)) out.push(sel + ' sem ícone: ' + e.textContent.trim().slice(0, 40));
    });
  }
  // Caixas de ícone vazias.
  document.querySelectorAll('.ss-icon, .waiting-icon-bg').forEach(e => {
    if (vis(e) && !tem(e)) out.push('caixa de ícone vazia: .' + [...e.classList].join('.'));
  });
  // Cabeçalho de tabela: o padrão é sem ícone.
  document.querySelectorAll('.table-head img').forEach(() => out.push('ícone em cabeçalho de tabela'));
  return [...new Set(out)];
}"""


@pytest.mark.parametrize("papel", PAPEIS)
def test_icones_consistentes(navegador, papel):
    ctx, pg = abrir(navegador, 1280, "light", papel)
    achados = []
    for pagina in _todas(papel):
        ir(pg, pagina)
        achados += [f"{pagina}: {a}" for a in pg.evaluate(ICONES_FALTANDO)]
    ctx.close()
    assert not achados, "\n".join(achados)


def test_icones_das_telas_de_espera(navegador):
    ctx, pg = abrir(navegador, 1280, "light")
    achados = []
    for pagina in [p for p in PUBLICAS if "aguardando" in p]:
        ir(pg, pagina, 400)
        achados += [f"{pagina}: {a}" for a in pg.evaluate(ICONES_FALTANDO)]
    ctx.close()
    assert not achados, "\n".join(achados)


# ── Tema escuro: nada de fundo claro ──────────────────────────────────
FUNDOS_CLAROS = """() => {
  const lum = s => { const m = s.match(/[\\d.]+/g); if (!m) return 0;
    const [r, g, b] = m.map(Number); return (0.2126*r + 0.7152*g + 0.0722*b) / 255; };
  const alfa = s => s.split(',').length > 3 ? parseFloat(s.split(',')[3]) : 1;
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect(); if (r.width < 40 || r.height < 20) continue;
    const c = getComputedStyle(e);
    if (c.display === 'none' || c.visibility === 'hidden' || e.tagName === 'INPUT') continue;
    if (e.closest('.accessibility-widget')) continue;
    const cores = [c.backgroundColor, ...((c.backgroundImage.includes('gradient') && c.backgroundImage.match(/rgba?\\([^)]*\\)/g)) || [])];
    if (cores.some(k => alfa(k) > 0.5 && lum(k) > 0.8))
      out.push((e.tagName.toLowerCase() + '.' + [...e.classList].join('.')).slice(0, 50)
               + ' "' + e.textContent.trim().replace(/\\s+/g, ' ').slice(0, 30) + '"');
  }
  return [...new Set(out)];
}"""


def test_tema_escuro_sem_fundo_claro_nas_publicas(navegador):
    ctx, pg = abrir(navegador, 1280, "dark")
    achados = []
    for pagina in PUBLICAS:
        ir(pg, pagina, 400)
        achados += [f"{pagina}: {a}" for a in pg.evaluate(FUNDOS_CLAROS)]
    ctx.close()
    assert not achados, "\n".join(achados)


@pytest.mark.parametrize("papel", PAPEIS)
def test_tema_escuro_sem_fundo_claro(navegador, papel):
    ctx, pg = abrir(navegador, 1280, "dark", papel)
    achados = []
    for pagina in _todas(papel):
        ir(pg, pagina)
        achados += [f"{pagina}: {a}" for a in pg.evaluate(FUNDOS_CLAROS)]
    ctx.close()
    assert not achados, "\n".join(achados)


def test_hover_nao_deixa_faixa_clara_no_escuro(navegador):
    """O brilho do hover terminava parado no meio do item."""
    ctx, pg = abrir(navegador, 1180, "dark", "sindico")
    ir(pg, "pages/sindico/porteiros.html", 1200)
    item = pg.locator(".list-item").first
    item.hover()
    pg.wait_for_timeout(1500)   # a animação dura 1 s
    opacidade_faixa = pg.evaluate("""() => {
      const e = document.querySelector('.list-item:hover');
      const cor = getComputedStyle(e, '::after').backgroundImage;
      const alfas = (cor.match(/rgba\\([^)]*\\)/g) || []).map(k => parseFloat(k.split(',')[3]));
      return Math.max(0, ...alfas);
    }""")
    ctx.close()
    assert opacidade_faixa <= 0.1


# ── Senha do cadastro segue as regras do servidor ─────────────────────
@pytest.mark.parametrize("senha,regras,nivel", [
    ("abc", "·✓·", "Fraca"),
    ("abcdefgh", "✓✓·", "Média"),
    ("abcdefg1", "✓✓✓", "Boa"),
    ("abcdefgh1234!", "✓✓✓", "Forte"),
])
def test_medidor_de_senha_do_cadastro(navegador, senha, regras, nivel):
    ctx, pg = abrir(navegador)
    ir(pg, "pages/cadastro/morador.html", 600)
    pg.evaluate("document.querySelectorAll('[id^=step]').forEach(s => s.style.display = 'none');"
                "document.getElementById('mSenha').closest('[id^=step]').style.display = 'block'")
    pg.fill("#mSenha", senha)
    marcadas = pg.evaluate("[...document.querySelectorAll('.pwd-req')]"
                           ".map(e => e.classList.contains('ok') ? '✓' : '·').join('')")
    texto_nivel = pg.inner_text("#pwdNivel")
    ctx.close()
    assert (marcadas, texto_nivel) == (regras, nivel)


# ── Logo ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("papel", PAPEIS)
def test_logo_leva_ao_painel_do_papel(navegador, papel):
    ctx, pg = abrir(navegador, 1280, "light", papel)
    outra = next(p for p in _todas(papel) if not p.endswith("dashboard.html"))
    ir(pg, outra, 400)
    pg.click(".app-bar-brand")
    pg.wait_for_url(f"**/pages/{papel}/dashboard.html", timeout=8000)
    # No próprio painel, a logo só recarrega a página.
    pg.click(".app-bar-brand")
    pg.wait_for_url(f"**/pages/{papel}/dashboard.html", timeout=8000)
    ctx.close()


# ── Mensagens ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("papel", ("sindico", "porteiro", "morador"))
def test_botao_de_mensagens_aparece(navegador, papel):
    ctx, pg = abrir(navegador, 1280, "light", papel)
    pg.wait_for_timeout(800)
    visivel = pg.is_visible(".chat-abrir")
    ctx.close()
    assert visivel


def test_administrador_nao_tem_mensagens(navegador):
    ctx, pg = abrir(navegador, 1280, "light", "admin")
    pg.wait_for_timeout(800)
    existe = pg.locator(".chat-abrir").count()
    ctx.close()
    assert existe == 0
