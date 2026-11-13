/* Acordo de parcelamento: o cartão de cada acordo — o que foi negociado,
   as parcelas e a situação — igual para o síndico e para o morador. Na
   tela do síndico, também o formulário: o apartamento, as cobranças
   vencidas dele, o número de parcelas, a primeira data e se a multa e os
   juros são dispensados. Os valores finais vêm da API. */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;
  var el = formato.el, botao = formato.botao, data = formato.data, dinheiro = formato.dinheiro;

  var SITUACAO = {
    em_dia: ['Em dia', 'badge-ok'],
    em_atraso: ['Parcela em atraso', 'badge-alert'],
    quitado: ['Quitado', 'badge-neutral'],
    cancelado: ['Desfeito', 'badge-neutral']
  };
  var STATUS = { aberta: 'a vencer', vencida: 'vencida', paga: 'paga', cancelada: 'cancelada',
                 negociada: 'negociada' };

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    function campo(id) { return document.getElementById(id); }
    var vencidas = [];

    function cartao(a) {
      var caixa = el('article', 'form-card acordo ' + a.situacao);
      caixa.setAttribute('aria-label', 'Acordo nº ' + a.id);
      var topo = el('div', 'assembleia-topo');
      topo.appendChild(el('h3', null, 'Acordo nº ' + a.id + (papel === 'sindico' ? ' — apto ' + a.unidade : '')));
      var s = SITUACAO[a.situacao] || [a.situacao, 'badge-neutral'];
      topo.appendChild(el('span', 'badge ' + s[1], s[0]));
      caixa.appendChild(topo);
      caixa.appendChild(el('p', 'assembleia-periodo', dinheiro(a.total) + ' em ' + a.parcelas +
        (a.parcelas === 1 ? ' parcela' : ' parcelas') + ', a primeira em ' + data(a.primeiro_vencimento)));
      caixa.appendChild(el('p', 'plano-obs', 'Valor em atraso ' + dinheiro(a.principal) +
        (a.dispensou_encargos ? ' · multa e juros dispensados'
                              : ' + multa e juros ' + dinheiro(a.encargos))));
      if (a.observacao) caixa.appendChild(el('p', 'plano-obs', a.observacao));
      if (a.cancelado_em) {
        caixa.appendChild(el('p', 'plano-obs', 'Desfeito: ' + (a.motivo_cancelamento || '')));
      }

      var lista = el('ul', 'plano-historico-lista acordo-parcelas');
      lista.setAttribute('aria-label', 'Parcelas do acordo nº ' + a.id);
      a.lista_parcelas.forEach(function(p, i) {
        lista.appendChild(el('li', 'parcela-' + p.status, (i + 1) + 'ª — ' + data(p.vencimento) +
          ' — ' + dinheiro(p.valor) + ' — ' + (STATUS[p.status] || p.status)));
      });
      caixa.appendChild(lista);
      if (a.negociadas.length) {
        caixa.appendChild(el('p', 'comunicado-autor', 'Negociadas: ' + a.negociadas.map(function(c) {
          return c.descricao + ' (venc. ' + data(c.vencimento) + ')';
        }).join('; ')));
      }

      if (a.pode_cancelar) {
        var acoes = el('div', 'infracao-acoes');
        var desfazer = botao('Desfazer', 'Desfazer o acordo nº ' + a.id, 'perigo-texto');
        desfazer.addEventListener('click', function() {
          var motivo = prompt('Por que desfazer o acordo? As parcelas saem e as cobranças voltam ' +
                              'como eram. O apartamento recebe o motivo.', '');
          if (motivo === null) return;
          if (motivo.trim().length < 3) { alert('Informe o motivo.'); return; }
          desfazer.disabled = true;
          api.post('/financeiro/acordos/' + a.id + '/cancelamento', { motivo: motivo.trim() })
            .then(carregar)
            .catch(function(e) { desfazer.disabled = false; alert(e.message); });
        });
        acoes.appendChild(desfazer);
        caixa.appendChild(acoes);
      }
      return caixa;
    }

    function carregar() {
      var pedidos = [api.get('/financeiro/acordos')];
      if (campo('formAcordo')) pedidos.push(api.get('/financeiro/cobrancas?status=vencida'));
      return Promise.all(pedidos).then(function(r) {
        var acordos = r[0];
        var caixa = campo('listaAcordos');
        caixa.innerHTML = '';
        acordos.forEach(function(a) { caixa.appendChild(cartao(a)); });
        function quantos(s) { return acordos.filter(function(a) { return a.situacao === s; }).length; }
        if (campo('totAcordosEmDia')) campo('totAcordosEmDia').textContent = quantos('em_dia');
        if (campo('totAcordosAtraso')) campo('totAcordosAtraso').textContent = quantos('em_atraso');
        if (campo('totAcordosQuitados')) campo('totAcordosQuitados').textContent = quantos('quitado');
        if (campo('secaoAcordos')) campo('secaoAcordos').hidden = !acordos.length;
        campo('estadoAcordos').textContent = acordos.length ? '' : 'Nenhum acordo de parcelamento.';
        if (r[1]) {
          vencidas = r[1];
          preencherUnidades();
        }
      }).catch(function(e) { campo('estadoAcordos').textContent = e.message; });
    }

    /* ── Formulário do síndico ─────────────────────────────────── */
    function preencherUnidades() {
      var sel = campo('aUnidade');
      var escolhida = sel.value;
      while (sel.options.length > 1) sel.remove(1);
      var vistas = {};
      vencidas.forEach(function(c) {
        if (vistas[c.unidade_id]) return;
        vistas[c.unidade_id] = true;
        var op = document.createElement('option');
        op.value = c.unidade_id;
        op.textContent = 'Apto ' + c.unidade;
        sel.appendChild(op);
      });
      sel.value = vistas[escolhida] ? escolhida : '';
      mostrarCobrancas();
    }

    function mostrarCobrancas() {
      var caixa = campo('aCobrancas');
      caixa.innerHTML = '';
      var unidade = campo('aUnidade').value;
      var dela = vencidas.filter(function(c) { return String(c.unidade_id) === unidade; });
      if (!unidade) {
        caixa.appendChild(el('p', 'regras-aviso', vencidas.length
          ? 'Escolha o apartamento para ver as cobranças vencidas dele.'
          : 'Nenhum apartamento com cobrança vencida.'));
      }
      dela.forEach(function(c) {
        var rotulo = el('label', 'permissao-item');
        var marca = el('input');
        marca.type = 'checkbox';
        marca.value = c.id;
        marca.checked = true;
        marca.id = 'aCob' + c.id;
        rotulo.htmlFor = marca.id;
        marca.addEventListener('change', previa);
        rotulo.appendChild(marca);
        rotulo.appendChild(document.createTextNode(' ' + c.descricao + ' — venceu em ' +
          data(c.vencimento) + ' — ' + dinheiro(c.total_atualizado) + ' com multa e juros'));
        caixa.appendChild(rotulo);
      });
      previa();
    }

    function marcadas() {
      var ids = [];
      campo('aCobrancas').querySelectorAll('input[type=checkbox]:checked').forEach(function(m) {
        ids.push(+m.value);
      });
      return vencidas.filter(function(c) { return ids.indexOf(c.id) >= 0; });
    }

    function previa() {
      var lista = marcadas();
      var parcelas = Math.max(1, +campo('aParcelas').value || 1);
      var total = lista.reduce(function(soma, c) {
        return soma + (campo('aDispensar').checked ? Number(c.valor) - Number(c.total_pago)
                                                   : Number(c.total_atualizado));
      }, 0);
      campo('aPrevia').textContent = lista.length
        ? 'Hoje: ' + dinheiro(total) + ' em ' + parcelas + 'x de cerca de ' +
          dinheiro(total / parcelas) + '. O valor final é calculado ao fazer o acordo.'
        : '';
    }

    var form = campo('formAcordo');
    if (form) {
      campo('aUnidade').addEventListener('change', mostrarCobrancas);
      campo('aParcelas').addEventListener('input', previa);
      campo('aDispensar').addEventListener('change', previa);
      campo('aPrimeiro').min = formato.hojeIso();
      campo('aPrimeiro').max = formato.hojeIso(90);
      campo('aPrimeiro').value = formato.hojeIso(5);
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        var erro = campo('erroAcordo');
        erro.className = 'form-erro';
        erro.textContent = '';
        var corpo = {
          unidade_id: +campo('aUnidade').value || null,
          cobranca_ids: marcadas().map(function(c) { return c.id; }),
          parcelas: +campo('aParcelas').value,
          primeiro_vencimento: campo('aPrimeiro').value,
          dispensar_encargos: campo('aDispensar').checked,
          observacao: campo('aObservacao').value.trim() || null
        };
        if (!corpo.unidade_id) { erro.textContent = 'Escolha o apartamento.'; return; }
        if (!corpo.cobranca_ids.length) { erro.textContent = 'Marque as cobranças do acordo.'; return; }
        if (!(corpo.parcelas >= 1 && corpo.parcelas <= 24)) {
          erro.textContent = 'De 1 a 24 parcelas.'; return;
        }
        if (!corpo.primeiro_vencimento) { erro.textContent = 'Escolha a data da primeira parcela.'; return; }
        var b = this.querySelector('button[type=submit]');
        b.disabled = true;
        api.post('/financeiro/acordos', corpo).then(function(a) {
          form.reset();
          campo('aPrimeiro').value = formato.hojeIso(5);
          // O aviso só depois da lista nova: quem lê "feito" já vê o acordo
          // e as parcelas na tela.
          return carregar().then(function() {
            erro.className = 'form-erro sucesso';
            erro.textContent = 'Acordo nº ' + a.id + ' feito: ' + dinheiro(a.total) + ' em ' +
              a.parcelas + 'x. O apartamento recebe as parcelas nas cobranças.';
          });
        }).catch(function(e) { erro.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }

    if (campo('hdrName')) campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.acordos = { montar: montar };
})(window);
