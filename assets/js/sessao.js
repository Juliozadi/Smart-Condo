/* ═══════════════════════════════════════════════════════════════
   SmartCondo — sessão nas páginas autenticadas

   Carregue este arquivo (depois de api.js) em toda página interna. Ele:
     1. exige sessão e o papel correspondente à pasta da página;
     2. preenche nome e papel no cabeçalho com os dados reais;
     3. liga o botão "Sair" ao encerramento da sessão.

   As telas de "aguardando aprovação" ficam de fora do guarda: elas são
   mostradas logo após o cadastro, quando ainda não existe login.
   ═══════════════════════════════════════════════════════════════ */
(function(global) {
  'use strict';

  var api = global.SmartCondo && global.SmartCondo.api;
  if (!api) {
    console.error('SmartCondo: carregue assets/js/api.js antes de sessao.js.');
    return;
  }

  var ROTULOS = { morador: 'Morador', porteiro: 'Porteiro', sindico: 'Síndico' };

  // O papel exigido vem da pasta: /pages/<papel>/<arquivo>.html
  function papelDaPagina() {
    var m = global.location.pathname.match(/\/pages\/(morador|porteiro|sindico)\//);
    return m ? m[1] : null;
  }

  function ehTelaDeEspera() {
    return /aguardando_aprovacao\.html$/.test(global.location.pathname);
  }

  function preencherCabecalho(usuario) {
    // O nome aparece em #hdrName na maioria das telas e em .profile-name
    // nas demais; preenche os dois quando existirem.
    var porId = document.getElementById('hdrName');
    if (porId) porId.textContent = usuario.nome;

    document.querySelectorAll('.profile-name').forEach(function(el) {
      el.textContent = usuario.nome;
    });
    document.querySelectorAll('.profile-role').forEach(function(el) {
      el.textContent = ROTULOS[usuario.papel] || usuario.papel;
    });
  }

  function ligarLogout() {
    document.querySelectorAll('.logout-btn').forEach(function(botao) {
      botao.addEventListener('click', function(e) {
        e.preventDefault();
        api.sair();
      });
    });
  }

  function iniciar() {
    if (ehTelaDeEspera()) {
      ligarLogout();
      return;
    }

    var usuario = api.protegerPagina(papelDaPagina());
    // Sem usuário, protegerPagina já redirecionou: não mexe mais na tela.
    if (!usuario) return;

    preencherCabecalho(usuario);
    ligarLogout();

    global.SmartCondo.usuario = usuario;
    document.dispatchEvent(new CustomEvent('smartcondo:sessao', { detail: usuario }));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})(window);
