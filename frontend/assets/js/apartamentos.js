/* "Meus apartamentos" no perfil: a mesma pessoa em outro apartamento do
   condomínio — o síndico que também mora, o dono de mais de um
   apartamento. Cada um vira um perfil, que se escolhe no topo da tela.
   Para o síndico vale na hora; para os outros, o síndico aprova.
   A página põe <div id="meusApartamentos"></div> onde quer a seção. */
(function(global) {
  'use strict';
  var api = global.SmartCondo.api;
  var OCUPACAO = { proprietario: 'Proprietário', inquilino: 'Inquilino', coabitante: 'Mora junto' };

  function criar(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function rotuloUnidade(u) {
    return (u.bloco && u.bloco !== 'unico' ? 'Bloco ' + u.bloco + ' — ' : '') + 'Apto ' + u.numero;
  }

  // Depois de mudar os perfis, a sessão guardada precisa saber (a troca
  // de perfil no topo aparece ou some).
  function atualizarSessao() {
    return api.get('/auth/eu').then(function(eu) {
      api.sessao.abrir(api.sessao.token(), eu);
      global.SmartCondo.usuario = eu;
      if (eu.possui_outros_perfis && global.SmartCondo.perfis) global.SmartCondo.perfis.montar(eu);
      if (eu.possui_outros_perfis && !global.SmartCondo.perfis) {
        var s = document.createElement('script');
        s.src = api.base + 'assets/js/perfis.js';
        document.body.appendChild(s);
      }
    }).catch(function() {});
  }

  function montar(caixa) {
    caixa.className = 'p-card meus-apartamentos';
    var titulo = criar('h2');
    var icone = criar('img');
    icone.src = api.base + 'assets/img/icons/building.svg';
    icone.width = 16; icone.height = 16; icone.alt = '';
    titulo.appendChild(icone);
    titulo.appendChild(document.createTextNode(' Meus Apartamentos'));
    caixa.appendChild(titulo);
    var eu = api.sessao.usuario() || {};
    caixa.appendChild(criar('p', 'p-nota',
      'Mora no condomínio, ou é dono de mais de um apartamento? Acrescente aqui e troque de ' +
      'perfil no topo da tela, com o mesmo login. ' +
      (eu.papel === 'sindico' ? 'Como síndico, vale na hora.' : 'O síndico confirma.')));

    var lista = criar('div', 'apto-lista');
    lista.setAttribute('aria-live', 'polite');
    caixa.appendChild(lista);

    var form = criar('form', 'apto-form');
    form.noValidate = true;
    form.innerHTML =
      '<div class="p-grid">' +
      '<div class="form-group"><label for="aptoUnidade">Apartamento</label>' +
      '<select id="aptoUnidade" required><option value="">Carregando…</option></select></div>' +
      '<div class="form-group"><label for="aptoOcupacao">Você é</label>' +
      '<select id="aptoOcupacao"><option value="proprietario">Proprietário</option>' +
      '<option value="inquilino">Inquilino</option></select></div>' +
      '</div>' +
      '<label class="apto-reside"><input type="checkbox" id="aptoReside" checked> Moro neste apartamento</label>' +
      '<p class="p-nota apto-reside-nota">Sem morar, você acompanha as cobranças e vota nas ' +
      'assembleias; visitas, encomendas, reservas e mudanças ficam com quem mora lá.</p>' +
      '<p class="form-erro" id="erroApto" role="alert"></p>' +
      '<button type="submit" class="action-btn compacto">Acrescentar apartamento</button>';
    caixa.appendChild(form);

    function carregar() {
      return api.get('/auth/perfis').then(function(perfis) {
        lista.innerHTML = '';
        var aptos = perfis.filter(function(p) { return p.papel === 'morador'; });
        if (!aptos.length) {
          lista.appendChild(criar('p', 'estado-lista', 'Nenhum apartamento no seu cadastro.'));
        }
        aptos.forEach(function(p, i) {
          var linha = criar('div', 'apto-item');
          var info = criar('div', 'apto-info');
          info.appendChild(criar('strong', null, 'Apto ' + p.unidade));
          info.appendChild(criar('span', null,
            (OCUPACAO[p.tipo_ocupacao] || 'Morador') + (p.reside ? '' : ' · não mora') +
            (p.status === 'ativo' ? '' : ' · aguardando o síndico')));
          linha.appendChild(info);
          // O apartamento do login não sai por aqui (é com o síndico).
          var doLogin = i === 0 && perfis[0].papel === 'morador';
          if (!doLogin) {
            var tirar = criar('button', 'contato-btn perigo-texto', 'Tirar');
            tirar.type = 'button';
            tirar.setAttribute('aria-label', 'Tirar o apartamento ' + p.unidade + ' do cadastro');
            tirar.addEventListener('click', function() {
              if (!confirm('Tirar o apartamento ' + p.unidade + ' do seu cadastro?')) return;
              tirar.disabled = true;
              api.remover('/usuarios/eu/apartamentos/' + p.usuario_id)
                .then(function() { return carregar(); })
                .then(atualizarSessao)
                .catch(function(e) { tirar.disabled = false; alert(e.message); });
            });
            linha.appendChild(tirar);
          }
          lista.appendChild(linha);
        });
      }).catch(function(e) {
        lista.innerHTML = '';
        lista.appendChild(criar('p', 'estado-lista', e.message));
      });
    }

    api.get('/condominios/meu/unidades').then(function(unidades) {
      var select = form.querySelector('#aptoUnidade');
      select.innerHTML = '<option value="">Escolha</option>';
      unidades.forEach(function(u) {
        var op = criar('option', null, rotuloUnidade(u));
        op.value = u.id;
        select.appendChild(op);
      });
    }).catch(function() {});

    form.addEventListener('submit', function(evento) {
      evento.preventDefault();
      var erro = form.querySelector('#erroApto');
      erro.className = 'form-erro';
      erro.textContent = '';
      var unidade = form.querySelector('#aptoUnidade').value;
      if (!unidade) { erro.textContent = 'Escolha o apartamento.'; return; }
      var botao = form.querySelector('button[type=submit]');
      botao.disabled = true;
      api.post('/usuarios/eu/apartamentos', {
        unidade_id: +unidade,
        tipo_ocupacao: form.querySelector('#aptoOcupacao').value,
        reside: form.querySelector('#aptoReside').checked
      }).then(function(p) {
        erro.className = 'form-erro sucesso';
        erro.textContent = p.status === 'ativo'
          ? 'Apartamento ' + p.unidade + ' acrescentado. Troque de perfil no topo da tela.'
          : 'Pedido enviado. Quando o síndico confirmar, o apartamento ' + p.unidade +
            ' aparece na troca de perfil.';
        form.reset();
        return carregar().then(atualizarSessao);
      }).catch(function(e) { erro.textContent = e.message; })
        .then(function() { botao.disabled = false; });
    });

    carregar();
  }

  var caixa = document.getElementById('meusApartamentos');
  if (caixa) montar(caixa);
})(window);
