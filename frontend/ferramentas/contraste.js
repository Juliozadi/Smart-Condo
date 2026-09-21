/* Mede o contraste de todo texto visível das páginas, nos dois temas,
 * e lista o que não alcança o mínimo do WCAG AA (documentação, seção
 * 12.1): 4,5:1 para texto normal e 3:1 para texto grande.
 *
 * Antes de rodar, deixe no ar a API (porta 8000) e o front-end
 * (porta 8080, servido de frontend/). Depois:
 *
 *   npm install playwright
 *   node ferramentas/contraste.js
 *
 * Fundos em gradiente são pulados: não dá para apurar a razão com
 * honestidade quando a cor varia ao longo do elemento. */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ORIGEM = 'http://127.0.0.1:8080';
const API = 'http://127.0.0.1:8000/api/v1';

// Função rodada dentro da página: mede o contraste de cada texto visível.
function medir() {
  const lum = ([r, g, b]) => {
    const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const razao = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };
  const rgba = (s) => {
    const m = (s || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(Number);
    return { cor: [p[0], p[1], p[2]], alfa: p.length > 3 ? p[3] : 1 };
  };
  // Mistura cor de frente com alfa sobre o fundo já resolvido.
  const sobrepor = (frente, alfa, fundo) =>
    frente.map((c, i) => Math.round(c * alfa + fundo[i] * (1 - alfa)));

  const resultado = [];
  const todos = document.body.querySelectorAll('*');
  for (const el of todos) {
    // Só elementos com texto próprio (não herdado de filhos).
    const texto = Array.from(el.childNodes)
      .filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(' ').trim();
    if (!texto) continue;

    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) continue;

    const frente = rgba(cs.color);
    if (!frente) continue;

    // Resolve o fundo subindo pelos ancestrais.
    let fundo = null, gradiente = false, no = el;
    while (no && no !== document.documentElement.parentNode) {
      const c = getComputedStyle(no);
      if (c.backgroundImage && c.backgroundImage !== 'none') { gradiente = true; break; }
      const bg = rgba(c.backgroundColor);
      if (bg && bg.alfa === 1) { fundo = bg.cor; break; }
      if (bg && bg.alfa > 0) {
        // fundo semitransparente: continua subindo e mistura depois
        const pai = no.parentElement;
        if (!pai) break;
        const cp = getComputedStyle(pai);
        if (cp.backgroundImage && cp.backgroundImage !== 'none') { gradiente = true; break; }
        const bgp = rgba(cp.backgroundColor);
        if (bgp && bgp.alfa === 1) { fundo = sobrepor(bg.cor, bg.alfa, bgp.cor); break; }
      }
      no = no.parentElement;
    }
    // Gradiente ou fundo indeterminado: não dá para medir com honestidade.
    if (gradiente || !fundo) continue;

    const corFinal = frente.alfa < 1 ? sobrepor(frente.cor, frente.alfa, fundo) : frente.cor;
    const tam = parseFloat(cs.fontSize);
    const peso = parseInt(cs.fontWeight, 10) || 400;
    const grande = tam >= 24 || (tam >= 18.66 && peso >= 700);
    const minimo = grande ? 3 : 4.5;
    const rz = razao(corFinal, fundo);
    if (rz < minimo) {
      resultado.push({
        seletor: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string'
          ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : ''),
        texto: texto.slice(0, 45),
        cor: cs.color, fundo: 'rgb(' + fundo.join(',') + ')',
        razao: Math.round(rz * 100) / 100, minimo,
      });
    }
  }
  return resultado;
}

// Varre frontend/ atrás das páginas e deduz o papel pela pasta.
function listarPaginas(raiz) {
  const achadas = [{ url: '/index.html', papel: null }];
  const PAPEIS = ['morador', 'porteiro', 'sindico', 'admin'];
  const andar = (dir, prefixo) => {
    for (const nome of fs.readdirSync(dir)) {
      const cheio = path.join(dir, nome);
      if (fs.statSync(cheio).isDirectory()) andar(cheio, prefixo + '/' + nome);
      else if (nome.endsWith('.html')) {
        const pasta = path.basename(dir);
        achadas.push({ url: prefixo + '/' + nome, papel: PAPEIS.includes(pasta) ? pasta : null });
      }
    }
  };
  andar(path.join(raiz, 'pages'), '/pages');
  return achadas;
}

async function entrar(papel) {
  const r = await fetch(API + '/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: papel + '@smartcondo.com', senha: 'smartcondo123' }),
  });
  if (!r.ok) throw new Error('login de ' + papel + ' falhou (' + r.status + '). A API está no ar?');
  const d = await r.json();
  return { token: d.access_token, usuario: d.usuario };
}

(async () => {
  const raiz = path.join(__dirname, '..');
  const paginas = listarPaginas(raiz);
  const tokens = {};
  for (const papel of ['admin', 'sindico', 'porteiro', 'morador']) tokens[papel] = await entrar(papel);
  const nav = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const achados = [];

  for (const tema of ['claro', 'escuro']) {
    for (const { url, papel } of paginas) {
      const ctx = await nav.newContext();
      const sessao = tokens[papel];
      await ctx.addInitScript(([s, t]) => {
        if (s) {
          localStorage.setItem('smartcondo_token', s.token);
          localStorage.setItem('smartcondo_usuario', JSON.stringify(s.usuario));
        }
        localStorage.setItem('smartcondo_acessibilidade', JSON.stringify({ tema: t }));
      }, [sessao || null, tema]);
      const p = await ctx.newPage();
      try {
        await p.goto(ORIGEM + url, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await p.waitForTimeout(1200);
        const falhas = await p.evaluate(medir);
        for (const f of falhas) achados.push({ tema, url, ...f });
      } catch (e) {
        console.error('ERRO', url, tema, e.message.slice(0, 60));
      }
      await ctx.close();
    }
  }
  await nav.close();
  const saida = path.join(__dirname, 'contraste-achados.json');
  fs.writeFileSync(saida, JSON.stringify(achados, null, 1));

  if (!achados.length) {
    console.log('Nenhuma falha: todo texto medido passa no WCAG AA nos dois temas.');
    return;
  }
  console.log(achados.length + ' falhas (detalhe em ' + saida + '):\n');
  const porCausa = new Map();
  for (const a of achados) {
    const chave = a.tema + ' | ' + a.cor + ' sobre ' + a.fundo;
    if (!porCausa.has(chave)) porCausa.set(chave, { n: 0, razao: a.razao, onde: a.seletor });
    porCausa.get(chave).n++;
  }
  for (const [chave, v] of [...porCausa].sort((a, b) => b[1].n - a[1].n)) {
    console.log(`  ${String(v.n).padStart(4)}x  razão ${v.razao}  ${chave}  (ex.: ${v.onde})`);
  }
  process.exitCode = 1;
})();
