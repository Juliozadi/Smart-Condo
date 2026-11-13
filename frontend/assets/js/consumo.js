/* Medição de água e gás. A equipe (síndico, ou o porteiro a quem ele
   liberou as leituras) lança a leitura do mês de cada apartamento numa
   grade só, vendo o consumo enquanto digita; o síndico gera a cobrança
   pela tarifa. O morador vê o histórico do apartamento e o aviso de
   consumo fora do normal. Os valores que contam são os da API. */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;
  var el = formato.el, dinheiro = formato.dinheiro;

  var NOME = { agua: 'água', gas: 'gás' };

  function m3(valor) {
    if (valor === null || valor === undefined || valor === '') return '—';
    return Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 3 }) + ' m³';
  }
  function mes(iso) { return iso ? iso.slice(5, 7) + '/' + iso.slice(0, 4) : ''; }
  function mesAtual() { return formato.hojeIso().slice(0, 7); }

  function montarEquipe(api, papel, campo) {
    var linhas = [];

    function competencia() { return campo('cCompetencia').value + '-01'; }

    function situacao(l) {
      if (l.cobrada) return ['Cobrada: ' + dinheiro(l.valor_cobrado), 'badge-neutral'];
      if (l.acima_do_normal) return ['Acima do normal', 'badge-alert'];
      if (l.leitura !== null && l.consumo === null) return ['Primeira leitura', 'badge-neutral'];
      if (l.leitura !== null) return ['Lida', 'badge-ok'];
      return ['Sem leitura', 'badge-neutral'];
    }

    function previa(l, entrada, troca, saida) {
      var v = entrada.value === '' ? null : Number(entrada.value);
      if (v === null) { saida.textContent = l.consumo === null ? '—' : m3(l.consumo); return; }
      if (troca.checked) { saida.textContent = m3(v); return; }
      if (l.anterior_leitura === null) { saida.textContent = 'ponto de partida'; return; }
      var consumo = v - Number(l.anterior_leitura);
      saida.textContent = consumo < 0 ? 'menor que a anterior' : m3(consumo);
    }

    function desenhar() {
      var tabela = campo('tabelaLeituras');
      var cabecalho = tabela.querySelector('.table-head');
      tabela.innerHTML = '';
      tabela.appendChild(cabecalho);
      linhas.forEach(function(l) {
        var linha = el('div', 'table-row cols-leitura' + (l.acima_do_normal ? ' alerta' : ''));
        linha.appendChild(el('span', 'leitura-apto', 'Apto ' + l.apartamento));
        linha.appendChild(el('span', null, l.anterior_leitura === null ? '—' :
          m3(l.anterior_leitura) + ' em ' + mes(l.anterior_competencia)));
        var celula = el('span');
        var entrada = el('input');
        entrada.type = 'number';
        entrada.min = '0';
        entrada.step = '0.001';
        entrada.inputMode = 'decimal';
        entrada.setAttribute('aria-label', 'Leitura do apto ' + l.apartamento);
        entrada.value = l.leitura === null ? '' : Number(l.leitura);
        entrada.disabled = !l.pode_editar;
        entrada.dataset.unidade = l.unidade_id;
        celula.appendChild(entrada);
        linha.appendChild(celula);
        var celTroca = el('span');
        var troca = el('input');
        troca.type = 'checkbox';
        troca.checked = !!l.troca_medidor;
        troca.disabled = !l.pode_editar;
        troca.setAttribute('aria-label', 'Medidor trocado no apto ' + l.apartamento);
        celTroca.appendChild(troca);
        linha.appendChild(celTroca);
        var consumo = el('span', 'leitura-consumo');
        linha.appendChild(consumo);
        var s = situacao(l);
        var celSituacao = el('span');
        celSituacao.appendChild(el('span', 'badge ' + s[1], s[0]));
        if (l.media !== null) celSituacao.appendChild(el('small', 'lista-autoria', 'média ' + m3(l.media)));
        linha.appendChild(celSituacao);
        l._entrada = entrada;
        l._troca = troca;
        var atualizar = function() { previa(l, entrada, troca, consumo); };
        entrada.addEventListener('input', atualizar);
        troca.addEventListener('change', atualizar);
        atualizar();
        tabela.appendChild(linha);
      });
      campo('estadoLeituras').textContent = linhas.length ? '' : 'Nenhuma unidade cadastrada.';
    }

    function carregar() {
      campo('estadoLeituras').textContent = 'Carregando…';
      return api.get('/consumo/leituras?tipo=' + campo('cTipo').value + '&competencia=' + competencia())
        .then(function(lista) { linhas = lista; desenhar(); })
        .catch(function(e) { campo('estadoLeituras').textContent = e.message; });
    }

    campo('cCompetencia').max = mesAtual();
    campo('cCompetencia').value = mesAtual();
    campo('cTipo').addEventListener('change', carregar);
    campo('cCompetencia').addEventListener('change', function() {
      if (campo('cCompetencia').value) carregar();
    });

    campo('formLeituras').addEventListener('submit', function(evento) {
      evento.preventDefault();
      var erro = campo('erroLeituras');
      erro.className = 'form-erro';
      erro.textContent = '';
      var itens = linhas.filter(function(l) {
        return l.pode_editar && l._entrada.value !== '' &&
          (l.leitura === null || Number(l._entrada.value) !== Number(l.leitura) ||
           l._troca.checked !== !!l.troca_medidor);
      }).map(function(l) {
        return { unidade_id: l.unidade_id, leitura: l._entrada.value, troca_medidor: l._troca.checked };
      });
      if (!itens.length) { erro.textContent = 'Nenhuma leitura nova ou alterada para salvar.'; return; }
      var b = campo('btnSalvarLeituras');
      b.disabled = true;
      api.post('/consumo/leituras', { tipo: campo('cTipo').value, competencia: competencia(), leituras: itens })
        .then(function(lista) {
          linhas = lista;
          desenhar();
          var alertas = lista.filter(function(l) { return l.acima_do_normal; }).length;
          erro.className = 'form-erro sucesso';
          erro.textContent = itens.length + (itens.length === 1 ? ' leitura salva' : ' leituras salvas') +
            (alertas ? ' · ' + alertas + ' acima do normal: o apartamento foi avisado.' : '.');
        })
        .catch(function(e) { erro.textContent = e.message; })
        .then(function() { b.disabled = false; });
    });

    if (papel === 'sindico') {
      campo('formCobrar').addEventListener('submit', function(evento) {
        evento.preventDefault();
        var aviso = campo('erroCobrar');
        aviso.className = 'form-erro';
        aviso.textContent = '';
        var tarifa = campo('cTarifa').value;
        if (!(Number(tarifa) > 0)) { aviso.textContent = 'Informe a tarifa por m³.'; return; }
        var b = this.querySelector('button[type=submit]');
        b.disabled = true;
        api.post('/consumo/cobrancas', {
          tipo: campo('cTipo').value, competencia: competencia(), tarifa: tarifa,
          vencimento: campo('cVencimento').value || null
        }).then(function(r) {
          return carregar().then(function() {
            aviso.className = 'form-erro sucesso';
            aviso.textContent = r.geradas + (r.geradas === 1 ? ' cobrança gerada' : ' cobranças geradas') +
              ', ' + dinheiro(r.total) + (r.puladas.length ? ' · sem consumo a cobrar: apto ' +
              r.puladas.join(', ') : '') + '.';
          });
        }).catch(function(e) { aviso.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }
    carregar();
  }

  function montarMorador(api, campo) {
    ['agua', 'gas'].forEach(function(tipo) {
      var caixa = campo('historico-' + tipo);
      api.get('/consumo/historico?tipo=' + tipo).then(function(lista) {
        var tabela = campo('tabela-' + tipo);
        if (!lista.length) {
          campo('estado-' + tipo).textContent = 'Nenhuma leitura de ' + NOME[tipo] + ' do seu apartamento ainda.';
          tabela.hidden = true;
          return;
        }
        campo('estado-' + tipo).textContent = '';
        if (lista[0].acima_do_normal) {
          caixa.insertBefore(el('p', 'aviso-consumo', 'O consumo de ' + NOME[tipo] + ' em ' +
            mes(lista[0].competencia) + ' foi mais que o dobro da média dos meses anteriores. ' +
            'Pode ser um vazamento: confira torneiras, descargas e o registro.'), tabela);
        }
        lista.forEach(function(h) {
          var linha = el('div', 'table-row cols-4' + (h.acima_do_normal ? ' alerta' : ''));
          linha.appendChild(el('span', null, mes(h.competencia)));
          linha.appendChild(el('span', null, m3(h.leitura) + (h.troca_medidor ? ' (medidor novo)' : '')));
          linha.appendChild(el('span', null, h.consumo === null ? 'primeira leitura' : m3(h.consumo)));
          linha.appendChild(el('span', null, h.valor_cobrado === null ? '—' : dinheiro(h.valor_cobrado)));
          tabela.appendChild(linha);
        });
      }).catch(function(e) { campo('estado-' + tipo).textContent = e.message; });
    });
  }

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    function campo(id) { return document.getElementById(id); }
    if (campo('hdrName')) campo('hdrName').textContent = usuario.nome;
    if (papel === 'morador') montarMorador(api, campo);
    else montarEquipe(api, papel, campo);
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.consumo = { montar: montar };
})(window);
