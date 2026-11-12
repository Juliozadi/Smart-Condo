/* Obras e reformas (NBR 16280): o cartão de cada reforma e as ações de
   quem está vendo — o morador comunica, cancela e avisa que terminou; o
   síndico aprova (com as condições do regimento), recusa, prorroga e
   cancela a obra irregular; a portaria só vê as aprovadas no prazo. O que
   cada um pode fazer vem da API (pode_avaliar, pode_cancelar...). */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;
  var el = formato.el, botao = formato.botao, data = formato.data;

  var SITUACAO = {
    aguardando: ['Aguardando o síndico', 'badge-pending'],
    agendada: ['Aprovada', 'badge-ok'],
    em_andamento: ['Em andamento', 'badge-ok'],
    prazo_encerrado: ['Prazo encerrado', 'badge-alert'],
    recusada: ['Recusada', 'badge-alert'],
    cancelada: ['Cancelada', 'badge-neutral'],
    concluida: ['Concluída', 'badge-neutral']
  };

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    function campo(id) { return document.getElementById(id); }

    function enviar(b, caminho, corpo) {
      b.disabled = true;
      return api.post(caminho, corpo)
        .then(carregar)
        .catch(function(e) { b.disabled = false; alert(e.message); });
    }

    function formProrrogar(r, caixa) {
      var form = el('form', 'chave-retirada');
      form.noValidate = true;
      var g = el('div', 'form-group');
      var l = el('label', null, 'Novo fim previsto');
      var i = el('input');
      i.type = 'date';
      i.id = 'pFim' + r.id;
      i.min = r.fim;
      l.htmlFor = i.id;
      g.appendChild(l);
      g.appendChild(i);
      var erro = el('p', 'form-erro');
      erro.setAttribute('role', 'alert');
      var ok = el('button', 'action-btn compacto', 'Prorrogar até esta data');
      ok.type = 'submit';
      form.appendChild(g);
      form.appendChild(erro);
      form.appendChild(ok);
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        erro.textContent = '';
        if (!i.value) { erro.textContent = 'Escolha a nova data.'; return; }
        ok.disabled = true;
        api.post('/reformas/' + r.id + '/prorrogacao', { fim: i.value })
          .then(carregar)
          .catch(function(e) { erro.textContent = e.message; ok.disabled = false; });
      });
      caixa.appendChild(form);
      return form;
    }

    function cartao(r) {
      var apto = 'apto ' + r.unidade;
      var caixa = el('article', 'form-card reforma ' + r.situacao);
      caixa.setAttribute('aria-label', 'Reforma do ' + apto);
      var topo = el('div', 'assembleia-topo');
      topo.appendChild(el('h3', null, papel === 'morador' ? 'Reforma' : 'Apto ' + r.unidade));
      var s = SITUACAO[r.situacao] || [r.situacao, 'badge-neutral'];
      topo.appendChild(el('span', 'badge ' + s[1], s[0]));
      caixa.appendChild(topo);
      caixa.appendChild(el('p', 'assembleia-periodo',
        'De ' + data(r.inicio) + ' a ' + data(r.fim) + (r.empresa ? ' · ' + r.empresa : '')));
      caixa.appendChild(el('p', 'plano-obs', r.descricao));
      if (r.altera_estrutura) {
        caixa.appendChild(el('p', 'plano-obs', 'Mexe em estrutura ou instalações · responsável ' +
          'técnico: ' + r.responsavel_tecnico + ' · ' + r.art_rrt));
      }
      if (papel === 'sindico' && r.solicitada_por_nome) {
        caixa.appendChild(el('p', 'comunicado-autor', 'Comunicada por ' + r.solicitada_por_nome));
      }
      if (r.condicoes) caixa.appendChild(el('p', 'reforma-condicoes', 'Condições: ' + r.condicoes));
      if (r.motivo_recusa) {
        caixa.appendChild(el('p', 'plano-obs', 'Motivo da recusa: ' + r.motivo_recusa));
      }
      if (r.status === 'cancelada') {
        caixa.appendChild(el('p', 'plano-obs', (r.cancelada_pelo_sindico
          ? 'Cancelada pelo síndico' : 'Cancelada pelo apartamento') +
          (r.motivo_cancelamento ? ': ' + r.motivo_cancelamento : '.')));
      }

      var acoes = el('div', 'infracao-acoes');
      if (r.pode_avaliar) {
        var aprovar = botao('Aprovar', 'Aprovar a reforma do ' + apto);
        aprovar.addEventListener('click', function() {
          var condicoes = prompt('Condições para a obra (opcional) — ex.: só das 8h às 17h; ' +
                                 'entulho em caçamba.', '');
          if (condicoes === null) return;
          enviar(aprovar, '/reformas/' + r.id + '/avaliacao',
                 { aprovada: true, condicoes: condicoes.trim() || null });
        });
        var recusar = botao('Recusar', 'Recusar a reforma do ' + apto, 'perigo-texto');
        recusar.addEventListener('click', function() {
          var motivo = prompt('Por que a reforma não pode ser feita assim? O apartamento recebe.', '');
          if (motivo === null) return;
          if (motivo.trim().length < 3) { alert('Informe o motivo da recusa.'); return; }
          enviar(recusar, '/reformas/' + r.id + '/avaliacao',
                 { aprovada: false, motivo: motivo.trim() });
        });
        acoes.appendChild(aprovar);
        acoes.appendChild(recusar);
      }
      if (r.pode_concluir) {
        var terminou = botao('Terminou', 'A reforma do ' + apto + ' terminou');
        terminou.addEventListener('click', function() {
          if (!confirm('Confirmar que a obra terminou? A portaria deixa de esperar os prestadores.')) return;
          enviar(terminou, '/reformas/' + r.id + '/conclusao', {});
        });
        acoes.appendChild(terminou);
      }
      var form = null;
      if (r.pode_prorrogar) {
        var prorrogar = botao('Prorrogar', 'Prorrogar a reforma do ' + apto);
        prorrogar.addEventListener('click', function() {
          if (!form) form = formProrrogar(r, caixa);
          else form.hidden = !form.hidden;
          if (!form.hidden) form.querySelector('input').focus();
        });
        acoes.appendChild(prorrogar);
      }
      if (r.pode_cancelar) {
        var cancelar = botao('Cancelar', 'Cancelar a reforma do ' + apto, 'perigo-texto');
        cancelar.addEventListener('click', function() {
          var corpo = {};
          if (papel === 'sindico') {
            var motivo = prompt('Motivo do cancelamento (ex.: obra sem a ART). O apartamento recebe.', '');
            if (motivo === null) return;
            if (motivo.trim().length < 3) { alert('Informe o motivo do cancelamento.'); return; }
            corpo.motivo = motivo.trim();
          } else if (!confirm('Cancelar esta reforma?')) {
            return;
          }
          enviar(cancelar, '/reformas/' + r.id + '/cancelamento', corpo);
        });
        acoes.appendChild(cancelar);
      }
      if (acoes.children.length) caixa.appendChild(acoes);
      return caixa;
    }

    function carregar() {
      return api.get('/reformas').then(function(lista) {
        var caixa = campo('listaReformas');
        caixa.innerHTML = '';
        lista.forEach(function(r) { caixa.appendChild(cartao(r)); });
        function quantas(s) { return lista.filter(function(r) { return r.situacao === s; }).length; }
        if (campo('totAndamento')) campo('totAndamento').textContent = quantas('em_andamento');
        if (campo('totAguardando')) campo('totAguardando').textContent = quantas('aguardando');
        if (campo('totAgendadas')) campo('totAgendadas').textContent = quantas('agendada');
        campo('estadoReformas').textContent = lista.length ? '' : (papel === 'porteiro'
          ? 'Nenhuma obra aprovada no momento.' : 'Nenhuma reforma comunicada.');
      }).catch(function(e) { campo('estadoReformas').textContent = e.message; });
    }

    var form = campo('formReforma');
    if (form) {
      var estrutura = campo('rEstrutura');
      estrutura.addEventListener('change', function() {
        campo('grupoTecnico').hidden = !this.checked;
      });
      campo('rInicio').min = formato.hojeIso(2);
      campo('rInicio').addEventListener('change', function() {
        campo('rFim').min = this.value;
      });
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        var erro = campo('erroReforma');
        erro.className = 'form-erro';
        erro.textContent = '';
        var corpo = {
          descricao: campo('rDescricao').value.trim(),
          empresa: campo('rEmpresa').value.trim() || null,
          inicio: campo('rInicio').value,
          fim: campo('rFim').value,
          altera_estrutura: estrutura.checked,
          responsavel_tecnico: estrutura.checked ? campo('rResponsavel').value.trim() || null : null,
          art_rrt: estrutura.checked ? campo('rArt').value.trim() || null : null
        };
        if (corpo.descricao.length < 10) { erro.textContent = 'Descreva o que será feito.'; return; }
        if (!corpo.inicio || !corpo.fim) { erro.textContent = 'Informe o início e o fim previsto.'; return; }
        if (corpo.fim < corpo.inicio) { erro.textContent = 'O fim precisa ser depois do início.'; return; }
        if (corpo.altera_estrutura && !(corpo.responsavel_tecnico && corpo.art_rrt)) {
          erro.textContent = 'Informe o responsável técnico e o número da ART ou do RRT.';
          return;
        }
        var b = this.querySelector('button[type=submit]');
        b.disabled = true;
        api.post('/reformas', corpo).then(function() {
          form.reset();
          campo('grupoTecnico').hidden = true;
          erro.className = 'form-erro sucesso';
          erro.textContent = 'Reforma comunicada. O síndico avalia e você recebe a resposta por e-mail.';
          return carregar();
        }).catch(function(e) { erro.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }

    campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.reformas = { montar: montar };
})(window);
