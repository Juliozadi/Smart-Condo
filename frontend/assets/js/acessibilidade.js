/* ═══════════════════════════════════════════════════════════════
   SmartCondo — Acessibilidade
   Documentação, seção 22:
     12.2 VLibras         — tradução para Libras (deficiência auditiva)
     12.3 Tamanho da fonte
     12.4 Mudança de cores — modo claro/escuro, seguindo por padrão a
                             definição do sistema operacional do usuário
   ═══════════════════════════════════════════════════════════════ */
(function() {
  'use strict';

  // As páginas ficam em profundidades diferentes (index.html na raiz,
  // pages/morador/x.html dois níveis abaixo). O caminho sai do src
  // deste próprio arquivo, que termina em "assets/js/": o que vem
  // antes é a raiz. Assim não importa de que pasta o site é servido
  // nem se a página foi aberta direto do disco.
  var BASE = (function() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute('src') || '';
      var corte = src.indexOf('assets/js/');
      if (corte !== -1) return src.slice(0, corte);
    }
    return '';
  })();

  var STORAGE_KEY = 'smartcondo_acessibilidade';
  var TEMAS = ['auto', 'claro', 'escuro'];

  /* ── Preferências ───────────────────────────────────────────── */
  function getPrefs() {
    try {
      var p = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
      if (TEMAS.indexOf(p.tema) === -1) p.tema = 'auto';
      return p;
    } catch (_) { return { tema: 'auto' }; }
  }

  function savePrefs(prefs) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)); } catch (_) {}
  }

  /* ── Tema (12.4) ────────────────────────────────────────────── */
  var mqEscuro = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  // "auto" = o que o sistema operacional do usuário estiver usando
  function temaEscuroAtivo(tema) {
    if (tema === 'escuro') return true;
    if (tema === 'claro') return false;
    return !!(mqEscuro && mqEscuro.matches);
  }

  function aplicarTema(tema) {
    if (!document.body) return;
    document.body.classList.toggle('tema-escuro', temaEscuroAtivo(tema));
  }

  // Aplicado já na execução do script (antes do DOMContentLoaded) para
  // reduzir o flash de tema claro em quem usa o SO no modo escuro.
  var prefsIniciais = getPrefs();
  aplicarTema(prefsIniciais.tema);

  // O usuário "pode alterar a qualquer momento" o modo do SO (doc 12.4):
  // enquanto o tema estiver em "auto", a página acompanha a mudança.
  if (mqEscuro) {
    var onMudancaSO = function() {
      if (getPrefs().tema === 'auto') aplicarTema('auto');
    };
    if (mqEscuro.addEventListener) mqEscuro.addEventListener('change', onMudancaSO);
    else if (mqEscuro.addListener) mqEscuro.addListener(onMudancaSO);
  }

  function applyPrefs(prefs) {
    document.body.classList.toggle('font-grande', !!prefs.fontGrande);
    document.body.classList.toggle('alto-contraste', !!prefs.altoContraste);
    document.body.classList.toggle('modo-leitura', !!prefs.modoLeitura);
    aplicarTema(prefs.tema);
  }

  /* ── VLibras (12.2) ─────────────────────────────────────────── */
  // Injetado aqui para valer nas 33 páginas sem duplicar markup.
  function injectVLibras() {
    if (document.querySelector('[vw]')) return;

    var wrapper = document.createElement('div');
    wrapper.setAttribute('vw', '');
    wrapper.className = 'enabled';
    wrapper.innerHTML =
      '<div vw-access-button class="active"></div>' +
      '<div vw-plugin-wrapper><div class="vw-plugin-top-wrapper"></div></div>';
    document.body.appendChild(wrapper);

    var script = document.createElement('script');
    script.src = 'https://vlibras.gov.br/app/vlibras-plugin.js';
    script.async = true;
    script.onload = function() {
      try { new window.VLibras.Widget('https://vlibras.gov.br/app'); } catch (_) {}
    };
    // Sem rede (ex.: aberto via file://) o widget some e o resto da página segue normal.
    script.onerror = function() { wrapper.remove(); };
    document.body.appendChild(script);
  }

  /* ── Widget de acessibilidade ───────────────────────────────── */
  function injectWidget() {
    var existing = document.querySelector('.accessibility-widget');
    if (existing) existing.remove();

    var html =
      '<div class="accessibility-widget" role="region" aria-label="Ferramentas de acessibilidade">' +
        '<input type="checkbox" id="access-toggle" aria-label="Abrir menu de acessibilidade">' +
        '<label for="access-toggle" class="access-button" title="Abrir ferramentas de acessibilidade" aria-label="Abrir ferramentas de acessibilidade">' +
          '<img src="' + BASE + 'assets/img/acessibilidade.png" class="access-icon-img" alt="" aria-hidden="true">' +
        '</label>' +
        '<div class="access-menu" role="menu" aria-label="Opções de acessibilidade">' +
          '<label role="menuitem" tabindex="0"><input type="checkbox" id="font-toggle"> Aumentar fonte</label>' +
          '<label role="menuitem" tabindex="0"><input type="checkbox" id="contrast-toggle"> Alto contraste</label>' +
          '<label role="menuitem" tabindex="0"><input type="checkbox" id="read-toggle"> Modo leitura</label>' +
          '<div class="access-theme" role="radiogroup" aria-label="Modo de cor">' +
            '<span class="access-theme-label">Modo de cor</span>' +
            '<div class="access-theme-opts">' +
              '<button type="button" class="access-theme-btn" data-tema="auto" role="radio" aria-checked="false" title="Seguir o sistema operacional">Auto</button>' +
              '<button type="button" class="access-theme-btn" data-tema="claro" role="radio" aria-checked="false" title="Sempre claro">Claro</button>' +
              '<button type="button" class="access-theme-btn" data-tema="escuro" role="radio" aria-checked="false" title="Sempre escuro">Escuro</button>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    var temp = document.createElement('div');
    temp.innerHTML = html;
    document.body.appendChild(temp.firstElementChild);
  }

  function setupWidget() {
    var widget = document.querySelector('.accessibility-widget');
    if (!widget) return;

    var prefs = getPrefs();
    var fontToggle = document.getElementById('font-toggle');
    var contrastToggle = document.getElementById('contrast-toggle');
    var readToggle = document.getElementById('read-toggle');

    if (fontToggle) fontToggle.checked = !!prefs.fontGrande;
    if (contrastToggle) contrastToggle.checked = !!prefs.altoContraste;
    if (readToggle) readToggle.checked = !!prefs.modoLeitura;
    applyPrefs(prefs);

    var accessToggle = document.getElementById('access-toggle');
    if (accessToggle) {
      accessToggle.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.checked = !this.checked;
        }
      });
    }

    document.querySelectorAll('.access-menu label[tabindex]').forEach(function(label) {
      label.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          var cb = this.querySelector('input[type="checkbox"]');
          if (cb) {
            cb.checked = !cb.checked;
            cb.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }
      });
    });

    if (fontToggle) {
      fontToggle.addEventListener('change', function() {
        prefs.fontGrande = this.checked;
        savePrefs(prefs);
        document.body.classList.toggle('font-grande', this.checked);
      });
    }
    if (contrastToggle) {
      contrastToggle.addEventListener('change', function() {
        prefs.altoContraste = this.checked;
        savePrefs(prefs);
        document.body.classList.toggle('alto-contraste', this.checked);
      });
    }
    if (readToggle) {
      readToggle.addEventListener('change', function() {
        prefs.modoLeitura = this.checked;
        savePrefs(prefs);
        document.body.classList.toggle('modo-leitura', this.checked);
      });
    }

    // Seletor de modo de cor (12.4)
    var botoesTema = widget.querySelectorAll('.access-theme-btn');
    function marcarTema(tema) {
      botoesTema.forEach(function(btn) {
        var ativo = btn.getAttribute('data-tema') === tema;
        btn.classList.toggle('ativo', ativo);
        btn.setAttribute('aria-checked', ativo ? 'true' : 'false');
      });
    }
    marcarTema(prefs.tema);
    botoesTema.forEach(function(btn) {
      btn.addEventListener('click', function() {
        prefs.tema = this.getAttribute('data-tema');
        savePrefs(prefs);
        aplicarTema(prefs.tema);
        marcarTema(prefs.tema);
      });
    });
  }

  function iniciar() {
    injectWidget();
    setupWidget();
    injectVLibras();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
