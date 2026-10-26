/* Manutenção preventiva (tela do síndico): os planos, do que vence
   primeiro ao que vence por último; registrar a realização renova o prazo
   e pode lançar a despesa na prestação de contas. */
(function() {
  'use strict';
  var api = window.SmartCondo.api;
  var usuario = api.protegerPagina('sindico');
  if (!usuario) return;

  var editando = null;

  function campo(id) { return document.getElementById(id); }
  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function data(iso) { return iso ? String(iso).slice(0, 10).split('-').reverse().join('/') : ''; }
  function dinheiro(v) {
    return Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }
  function hojeIso() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }
  function selo(p) {
    if (p.situacao === 'vencida') {
      var ha = -p.dias_para_vencer;
      return ['Venceu há ' + ha + (ha === 1 ? ' dia' : ' dias'), 'badge-alert'];
    }
    if (p.situacao === 'vence_em_breve') {
      return [p.dias_para_vencer === 0 ? 'Vence hoje'
        : 'Vence em ' + p.dias_para_vencer + (p.dias_para_vencer === 1 ? ' dia' : ' dias'), 'badge-pending'];
    }
    return ['Em dia', 'badge-ok'];
  }
  function botao(texto, rotulo, classe) {
    var b = el('button', 'contato-btn' + (classe ? ' ' + classe : ''), texto);
    b.type = 'button';
    b.setAttribute('aria-label', rotulo);
    return b;
  }

  function formRealizacao(p, caixa) {
    var form = el('form', 'plano-realizacao');
    form.noValidate = true;
    form.hidden = true;
    form.innerHTML =
      '<div class="form-row">' +
      '<div class="form-group"><label></label><input type="date" required></div>' +
      '<div class="form-group"><label></label><input type="number" min="0.01" step="0.01" inputmode="decimal"></div>' +
      '</div>' +
      '<div class="form-group"><label></label><input type="text" maxlength="2000"></div>' +
      '<label class="permissao-item"><input type="checkbox"> Lançar o custo como despesa de manutenção</label>' +
      '<p class="form-erro" role="alert"></p>' +
      '<button class="action-btn compacto" type="submit">Salvar</button>';
    var rotulos = form.querySelectorAll('.form-group label');
    var entradas = form.querySelectorAll('.form-group input');
    [['rData', 'Quando foi feito'], ['rCusto', 'Custo (R$, opcional)'],
     ['rObs', 'Observação (opcional)']].forEach(function(par, i) {
      entradas[i].id = par[0] + p.id;
      rotulos[i].htmlFor = par[0] + p.id;
      rotulos[i].textContent = par[1];
    });
    var despesa = form.querySelector('input[type=checkbox]');
    despesa.id = 'rDespesa' + p.id;
    entradas[0].value = hojeIso();
    entradas[0].max = hojeIso();
    var erro = form.querySelector('.form-erro');

    form.addEventListener('submit', function(evento) {
      evento.preventDefault();
      erro.textContent = '';
      var corpo = {
        data: entradas[0].value,
        custo: entradas[1].value || null,
        observacao: entradas[2].value.trim() || null,
        lancar_despesa: despesa.checked
      };
      if (!corpo.data) { erro.textContent = 'Informe quando foi feito.'; return; }
      if (corpo.lancar_despesa && !corpo.custo) {
        erro.textContent = 'Para lançar a despesa, informe o custo.';
        return;
      }
      var enviar = form.querySelector('button[type=submit]');
      enviar.disabled = true;
      api.post('/manutencao-preventiva/' + p.id + '/realizacoes', corpo)
        .then(carregar)
        .catch(function(e) { erro.textContent = e.message; enviar.disabled = false; });
    });
    caixa.appendChild(form);
    return form;
  }

  function historico(p, caixa) {
    if (caixa.hidden === false) { caixa.hidden = true; return; }
    caixa.hidden = false;
    caixa.textContent = 'Carregando…';
    api.get('/manutencao-preventiva/' + p.id + '/realizacoes').then(function(lista) {
      caixa.innerHTML = '';
      if (!lista.length) { caixa.textContent = 'Nenhuma realização registrada ainda.'; return; }
      var ul = el('ul', 'plano-historico-lista');
      lista.forEach(function(r) {
        var partes = [data(r.data)];
        if (r.custo) partes.push(dinheiro(r.custo) + (r.despesa_id ? ' (lançado nas despesas)' : ''));
        if (r.registrada_por_nome) partes.push('por ' + r.registrada_por_nome);
        var li = el('li', null, partes.join(' · '));
        if (r.observacao) li.appendChild(el('span', 'plano-historico-obs', r.observacao));
        ul.appendChild(li);
      });
      caixa.appendChild(ul);
    }).catch(function(e) { caixa.textContent = e.message; });
  }

  function cartao(p) {
    var caixa = el('article', 'form-card plano ' + p.situacao);
    caixa.setAttribute('aria-label', p.nome);
    var topo = el('div', 'assembleia-topo');
    topo.appendChild(el('h3', null, p.nome));
    var s = selo(p);
    topo.appendChild(el('span', 'badge ' + s[1], s[0]));
    caixa.appendChild(topo);
    caixa.appendChild(el('p', 'assembleia-periodo',
      'A cada ' + p.periodicidade_meses + (p.periodicidade_meses === 1 ? ' mês' : ' meses') +
      ' · vence em ' + data(p.proximo_vencimento) +
      (p.ultima_realizacao ? ' · feito em ' + data(p.ultima_realizacao) : ' · ainda sem registro') +
      (p.fornecedor ? ' · ' + p.fornecedor : '')));
    if (p.observacao) caixa.appendChild(el('p', 'plano-obs', p.observacao));

    var acoes = el('div', 'infracao-acoes');
    var bRealizar = botao('Registrar realização', 'Registrar realização de ' + p.nome);
    var bHistorico = botao('Histórico', 'Histórico de ' + p.nome);
    var bEditar = botao('Editar', 'Editar ' + p.nome);
    var bRemover = botao('Remover', 'Remover ' + p.nome, 'perigo-texto');
    [bRealizar, bHistorico, bEditar, bRemover].forEach(function(b) { acoes.appendChild(b); });
    caixa.appendChild(acoes);

    var form = formRealizacao(p, caixa);
    var hist = el('div', 'plano-historico');
    hist.hidden = true;
    caixa.appendChild(hist);

    bRealizar.addEventListener('click', function() {
      form.hidden = !form.hidden;
      if (!form.hidden) form.querySelector('input').focus();
    });
    bHistorico.addEventListener('click', function() { historico(p, hist); });
    bEditar.addEventListener('click', function() { editar(p); });
    bRemover.addEventListener('click', function() {
      if (!confirm('Remover "' + p.nome + '"? O histórico fica guardado.')) return;
      bRemover.disabled = true;
      api.remover('/manutencao-preventiva/' + p.id)
        .then(carregar)
        .catch(function(e) { bRemover.disabled = false; alert(e.message); });
    });
    return caixa;
  }

  function carregar() {
    return api.get('/manutencao-preventiva').then(function(lista) {
      var conta = { vencida: 0, vence_em_breve: 0, em_dia: 0 };
      var caixa = campo('listaPlanos');
      caixa.innerHTML = '';
      lista.forEach(function(p) { conta[p.situacao]++; caixa.appendChild(cartao(p)); });
      campo('totVencidas').textContent = conta.vencida;
      campo('totEmBreve').textContent = conta.vence_em_breve;
      campo('totEmDia').textContent = conta.em_dia;
      campo('estadoPlanos').textContent = lista.length ? ''
        : 'Nenhum plano ainda. Cadastre abaixo o que vence de tempos em tempos.';
    }).catch(function(e) { campo('estadoPlanos').textContent = e.message; });
  }

  function limparForm() {
    editando = null;
    campo('formPlano').reset();
    campo('pAviso').value = 30;
    campo('btnSalvarPlano').textContent = 'Cadastrar';
    campo('btnCancelarEdicao').hidden = true;
    campo('tituloForm').lastChild.textContent = ' Novo Plano';
  }

  function editar(p) {
    editando = p;
    campo('pNome').value = p.nome;
    campo('pPeriodicidade').value = p.periodicidade_meses;
    campo('pVencimento').value = p.proximo_vencimento;
    campo('pAviso').value = p.antecedencia_aviso_dias;
    campo('pFornecedor').value = p.fornecedor || '';
    campo('pObservacao').value = p.observacao || '';
    campo('btnSalvarPlano').textContent = 'Salvar alterações';
    campo('btnCancelarEdicao').hidden = false;
    campo('tituloForm').lastChild.textContent = ' Editar Plano';
    campo('erroPlano').textContent = '';
    campo('tituloForm').scrollIntoView({ behavior: 'smooth' });
    campo('pNome').focus();
  }

  campo('btnCancelarEdicao').addEventListener('click', limparForm);

  campo('formPlano').addEventListener('submit', function(evento) {
    evento.preventDefault();
    var erro = campo('erroPlano');
    erro.className = 'form-erro';
    erro.textContent = '';
    var corpo = {
      nome: campo('pNome').value.trim(),
      periodicidade_meses: parseInt(campo('pPeriodicidade').value, 10),
      proximo_vencimento: campo('pVencimento').value,
      antecedencia_aviso_dias: parseInt(campo('pAviso').value || '30', 10),
      fornecedor: campo('pFornecedor').value.trim() || null,
      observacao: campo('pObservacao').value.trim() || null
    };
    if (corpo.nome.length < 3) { erro.textContent = 'Diga o que precisa ser feito.'; return; }
    if (!(corpo.periodicidade_meses >= 1 && corpo.periodicidade_meses <= 120)) {
      erro.textContent = 'A periodicidade vai de 1 a 120 meses.';
      return;
    }
    if (!corpo.proximo_vencimento) { erro.textContent = 'Informe o próximo vencimento.'; return; }
    var enviar = campo('btnSalvarPlano');
    enviar.disabled = true;
    var pedido = editando
      ? api.put('/manutencao-preventiva/' + editando.id, corpo)
      : api.post('/manutencao-preventiva', corpo);
    pedido.then(function(p) {
      limparForm();
      erro.className = 'form-erro sucesso';
      erro.textContent = '"' + p.nome + '" salvo. Próximo vencimento: ' + data(p.proximo_vencimento) + '.';
      return carregar();
    }).catch(function(e) { erro.textContent = e.message; })
      .then(function() { enviar.disabled = false; });
  });

  campo('hdrName').textContent = usuario.nome;
  carregar();
})();
