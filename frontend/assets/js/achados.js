/* Achados e perdidos: a portaria e o síndico registram o que foi achado e
   entregam a quem é dono; o morador vê o que está guardado e diz "é meu".
   O síndico doa ou descarta o que ninguém reclamou depois de 30 dias.
   Os dados de quem registrou e de quem reclamou só a equipe vê — a API
   nem os manda para o morador. */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;
  var el = formato.el, botao = formato.botao, data = formato.data, quando = formato.quando;

  var SITUACAO = {
    guardado: ['Guardado na portaria', 'badge-neutral'],
    devolvido: ['Entregue', 'badge-ok'],
    descartado: ['Doado ou descartado', 'badge-neutral']
  };

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    var equipe = papel !== 'morador';
    function campo(id) { return document.getElementById(id); }

    function acao(promessa, botoes) {
      botoes.forEach(function(b) { b.disabled = true; });
      return promessa.then(carregar).catch(function(e) {
        botoes.forEach(function(b) { b.disabled = false; });
        alert(e.message);
      });
    }

    function formEntrega(a, caixa) {
      var form = el('form', 'chave-retirada');
      form.noValidate = true;
      var g = el('div', 'form-group');
      var rotulo = el('label', null, 'Quem está retirando');
      rotulo.htmlFor = 'aEntregue' + a.id;
      var nome = el('input');
      nome.id = 'aEntregue' + a.id;
      nome.maxLength = 120;
      // Quem reclamou já vem preenchido; a portaria confere o documento.
      nome.value = a.reclamado_por ? a.reclamado_por.split(' — ')[0] : '';
      g.appendChild(rotulo);
      g.appendChild(nome);
      form.appendChild(g);
      var erro = el('p', 'form-erro');
      erro.setAttribute('role', 'alert');
      form.appendChild(erro);
      var enviar = el('button', 'action-btn compacto', 'Entregar');
      enviar.type = 'submit';
      form.appendChild(enviar);
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        erro.textContent = '';
        var quem = nome.value.trim();
        if (quem.length < 3) { erro.textContent = 'Informe quem está retirando.'; return; }
        enviar.disabled = true;
        api.post('/achados/' + a.id + '/devolucao', { entregue_a: quem })
          .then(carregar)
          .catch(function(e) { enviar.disabled = false; erro.textContent = e.message; });
      });
      caixa.appendChild(form);
      nome.focus();
    }

    function cartao(a) {
      var caixa = el('article', 'form-card achado ' + a.status + (a.reclamado ? ' reclamado' : ''));
      caixa.setAttribute('aria-label', a.descricao);
      var topo = el('div', 'assembleia-topo');
      topo.appendChild(el('h3', null, a.descricao));
      var s = SITUACAO[a.status] || [a.status, 'badge-neutral'];
      if (a.status === 'guardado' && a.reclamado) {
        s = [a.reclamado_por_mim ? 'Você disse que é seu' : 'Já tem dono — aguardando retirada', 'badge-alert'];
      }
      topo.appendChild(el('span', 'badge ' + s[1], s[0]));
      caixa.appendChild(topo);
      caixa.appendChild(el('p', 'assembleia-periodo', 'Achado em ' + data(a.encontrado_em) + ' — ' +
        a.local + (a.status === 'guardado' ? ' · guardado há ' + a.dias_guardado +
        (a.dias_guardado === 1 ? ' dia' : ' dias') : '')));
      if (equipe && a.registrado_por) caixa.appendChild(el('p', 'plano-obs', 'Registrado por ' + a.registrado_por));
      if (equipe && a.reclamado_por) {
        caixa.appendChild(el('p', 'chave-com', 'Reclamado por ' + a.reclamado_por +
          (a.reclamado_em ? ' em ' + quando(a.reclamado_em) : '')));
      }
      if (a.status === 'devolvido') {
        caixa.appendChild(el('p', 'plano-obs', 'Entregue a ' + a.entregue_a + ' em ' + quando(a.devolvido_em)));
      }
      if (a.status === 'descartado' && a.destino) {
        caixa.appendChild(el('p', 'plano-obs', 'Destino: ' + a.destino +
          (a.descartado_em ? ' (' + quando(a.descartado_em) + ')' : '')));
      }
      if (!equipe && a.reclamado_por_mim && a.status === 'guardado') {
        caixa.appendChild(el('p', 'plano-obs', 'Retire na portaria com um documento com foto.'));
      }

      var acoes = el('div', 'infracao-acoes');
      if (a.pode_reclamar) {
        var meu = botao('É meu', 'É meu: ' + a.descricao);
        meu.addEventListener('click', function() {
          acao(api.post('/achados/' + a.id + '/reclamacao', {}), [meu]);
        });
        acoes.appendChild(meu);
      }
      if (a.pode_desistir) {
        var naoE = botao('Não é meu', 'Não é meu: ' + a.descricao);
        naoE.addEventListener('click', function() {
          acao(api.remover('/achados/' + a.id + '/reclamacao'), [naoE]);
        });
        acoes.appendChild(naoE);
      }
      if (a.pode_devolver) {
        var entregar = botao('Entregar', 'Entregar: ' + a.descricao);
        entregar.addEventListener('click', function() {
          entregar.disabled = true;
          formEntrega(a, caixa);
        });
        acoes.appendChild(entregar);
      }
      if (a.pode_descartar) {
        var doar = botao('Doar ou descartar', 'Doar ou descartar: ' + a.descricao, 'perigo-texto');
        doar.addEventListener('click', function() {
          var destino = prompt('Para onde vai "' + a.descricao + '"? (ex: doado ao bazar da paróquia)', '');
          if (destino === null) return;
          if (destino.trim().length < 3) { alert('Informe o destino.'); return; }
          acao(api.post('/achados/' + a.id + '/descarte', { destino: destino.trim() }), [doar]);
        });
        acoes.appendChild(doar);
      }
      if (acoes.children.length) caixa.appendChild(acoes);
      return caixa;
    }

    function carregar() {
      var filtro = campo('filtroAchados') ? campo('filtroAchados').value : '';
      return api.get('/achados' + (filtro ? '?status=' + filtro : '')).then(function(lista) {
        var caixa = campo('listaAchados');
        caixa.innerHTML = '';
        lista.forEach(function(a) { caixa.appendChild(cartao(a)); });
        var guardados = lista.filter(function(a) { return a.status === 'guardado'; });
        if (campo('totGuardados')) campo('totGuardados').textContent = guardados.length;
        if (campo('totReclamados')) {
          campo('totReclamados').textContent = guardados.filter(function(a) { return a.reclamado; }).length;
        }
        campo('estadoAchados').textContent = lista.length ? '' : (equipe
          ? 'Nada por aqui.' : 'Nenhum objeto guardado na portaria agora.');
      }).catch(function(e) { campo('estadoAchados').textContent = e.message; });
    }

    var form = campo('formAchado');
    if (form) {
      campo('aEncontrado').max = formato.hojeIso();
      campo('aEncontrado').min = formato.hojeIso(-30);
      campo('aEncontrado').value = formato.hojeIso();
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        var erro = campo('erroAchado');
        erro.className = 'form-erro';
        erro.textContent = '';
        var corpo = {
          descricao: campo('aDescricao').value.trim(),
          local: campo('aLocal').value.trim(),
          encontrado_em: campo('aEncontrado').value
        };
        if (corpo.descricao.length < 3) { erro.textContent = 'Descreva o objeto.'; return; }
        if (corpo.local.length < 2) { erro.textContent = 'Informe onde foi achado.'; return; }
        if (!corpo.encontrado_em) { erro.textContent = 'Informe quando foi achado.'; return; }
        var b = this.querySelector('button[type=submit]');
        b.disabled = true;
        api.post('/achados', corpo).then(function() {
          form.reset();
          campo('aEncontrado').value = formato.hojeIso();
          erro.className = 'form-erro sucesso';
          erro.textContent = 'Registrado. Os moradores já veem o objeto na lista.';
          return carregar();
        }).catch(function(e) { erro.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }
    if (campo('filtroAchados')) campo('filtroAchados').addEventListener('change', carregar);
    if (campo('hdrName')) campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.achados = { montar: montar };
})(window);
