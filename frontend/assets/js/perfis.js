/* Troca de perfil: a mesma pessoa como síndico e como morador, ou em
   mais de um apartamento. Um botão na barra superior lista os perfis da
   pessoa; escolhido um, a API devolve a sessão dele, sem pedir a senha
   de novo, e a tela vai para o painel daquele perfil.
   Carregado por sessao.js só para quem tem mais de um perfil. */
(function(global) {
  'use strict';
  var api = global.SmartCondo.api;
  var ROTULO = { sindico: 'Síndico', morador: 'Morador', porteiro: 'Porteiro', admin: 'Administrador' };

  function criar(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function descrever(p) {
    if (p.papel !== 'morador') {
      return ROTULO[p.papel] + (p.condominio ? ' — ' + p.condominio : '');
    }
    var texto = 'Apto ' + p.unidade;
    if (!p.reside) texto += ' (proprietário, não mora)';
    return texto;
  }

  function rotuloAtual(usuario) {
    if (usuario.papel !== 'morador') return ROTULO[usuario.papel] || usuario.papel;
    var u = usuario.unidade;
    return u ? 'Apto ' + (u.bloco && u.bloco !== 'unico' ? u.bloco + ' ' : '') + u.numero
             : 'Morador';
  }

  function montar(usuario) {
    var destino = document.querySelector('.app-bar-right');
    if (!destino || document.querySelector('.perfil-trocar')) return;

    var caixa = criar('div', 'perfil-troca');
    var botao = criar('button', 'perfil-trocar');
    botao.type = 'button';
    botao.setAttribute('aria-haspopup', 'true');
    botao.setAttribute('aria-expanded', 'false');
    botao.setAttribute('aria-label', 'Trocar de perfil. Agora: ' + rotuloAtual(usuario));
    botao.title = 'Trocar de perfil';
    var img = criar('img');
    img.src = api.base + 'assets/img/icons/building.svg';
    img.alt = '';
    botao.appendChild(img);
    botao.appendChild(criar('span', 'perfil-trocar-texto', rotuloAtual(usuario)));

    var menu = criar('div', 'perfil-menu');
    menu.hidden = true;
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', 'Meus perfis');

    function fechar() {
      menu.hidden = true;
      botao.setAttribute('aria-expanded', 'false');
    }

    function escolher(p, item) {
      item.disabled = true;
      api.post('/auth/perfis/' + p.usuario_id, {})
        .then(function(r) {
          api.sessao.abrir(r.access_token, r.usuario);
          global.location.href = api.base + 'pages/' + r.usuario.papel + '/dashboard.html';
        })
        .catch(function(e) { item.disabled = false; alert(e.message); });
    }

    function abrir() {
      menu.innerHTML = '';
      menu.appendChild(criar('p', 'perfil-menu-titulo', 'Carregando…'));
      menu.hidden = false;
      botao.setAttribute('aria-expanded', 'true');
      api.get('/auth/perfis').then(function(lista) {
        menu.innerHTML = '';
        menu.appendChild(criar('p', 'perfil-menu-titulo', 'Entrar como'));
        lista.forEach(function(p) {
          var item = criar('button', 'perfil-menu-item' + (p.atual ? ' atual' : ''));
          item.type = 'button';
          item.setAttribute('role', 'menuitem');
          item.appendChild(criar('span', null, descrever(p)));
          if (p.atual) {
            item.appendChild(criar('small', null, 'agora'));
            item.disabled = true;
          } else if (p.status !== 'ativo') {
            item.appendChild(criar('small', null, 'aguardando o síndico'));
            item.disabled = true;
          } else {
            item.addEventListener('click', function() { escolher(p, item); });
          }
          menu.appendChild(item);
        });
        var primeiro = menu.querySelector('.perfil-menu-item:not([disabled])');
        if (primeiro) primeiro.focus();
      }).catch(function(e) {
        menu.innerHTML = '';
        menu.appendChild(criar('p', 'perfil-menu-titulo', e.message));
      });
    }

    botao.addEventListener('click', function() {
      if (menu.hidden) abrir(); else fechar();
    });
    document.addEventListener('click', function(e) {
      if (!caixa.contains(e.target)) fechar();
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && !menu.hidden) { fechar(); botao.focus(); }
    });

    caixa.appendChild(botao);
    caixa.appendChild(menu);
    destino.insertBefore(caixa, destino.firstChild);
    // Na barra estreita, o nome ao lado da foto cede o lugar ao botão.
    document.body.classList.add('com-perfis');
  }

  global.SmartCondo.perfis = { montar: montar };
  if (global.SmartCondo.usuario) montar(global.SmartCondo.usuario);
})(window);
