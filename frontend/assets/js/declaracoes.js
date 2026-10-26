/* Declaração de quitação: o cartão de cada declaração, igual para o
   morador e para o síndico, e o endereço da página pública em que
   qualquer um confere o código. Quem chama acrescenta o que é dele: o
   síndico, o botão de revogar. */
(function(global) {
  'use strict';

  var SITUACAO = {
    valida: ['Válida', 'badge-ok'],
    vencida: ['Vencida', 'badge-neutral'],
    revogada: ['Revogada', 'badge-alert']
  };

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function data(iso) { return iso ? String(iso).slice(0, 10).split('-').reverse().join('/') : ''; }
  function cnpj(valor) {
    var d = String(valor || '').replace(/\D/g, '');
    if (d.length !== 14) return valor || '';
    return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5, 8) + '/' + d.slice(8, 12) + '-' + d.slice(12);
  }
  function enderecoPublico(codigo) {
    return global.SmartCondo.api.base + 'pages/verificar/declaracao.html?codigo=' +
      encodeURIComponent(codigo);
  }

  function cartao(d, comQuemPediu) {
    var caixa = el('article', 'form-card declaracao');
    caixa.setAttribute('aria-label', 'Declaração do apartamento ' + d.unidade + ' de ' +
      data(d.referencia_ate));
    var topo = el('div', 'assembleia-topo');
    topo.appendChild(el('h3', null, 'Apto ' + d.unidade + ' — ' + data(d.referencia_ate)));
    var s = SITUACAO[d.situacao] || [d.situacao, 'badge-neutral'];
    topo.appendChild(el('span', 'badge ' + s[1], s[0]));
    caixa.appendChild(topo);

    caixa.appendChild(el('p', 'assembleia-periodo',
      'Sem débito vencido até ' + data(d.referencia_ate) + ' · válida até ' + data(d.valida_ate) +
      (comQuemPediu && d.emitida_por_nome ? ' · pedida por ' + d.emitida_por_nome : '')));
    var codigo = el('p', 'declaracao-codigo');
    codigo.appendChild(el('span', null, 'Código de verificação: '));
    codigo.appendChild(el('strong', null, d.codigo));
    caixa.appendChild(codigo);
    if (d.situacao === 'revogada') {
      caixa.appendChild(el('p', 'infracao-decisao', 'Revogada pelo síndico em ' + data(d.revogada_em) +
        (d.motivo_revogacao ? ': ' + d.motivo_revogacao : '.')));
    }

    var acoes = el('div', 'infracao-acoes');
    var abrir = el('a', 'contato-btn', 'Abrir a declaração');
    abrir.href = enderecoPublico(d.codigo);
    abrir.target = '_blank';
    abrir.rel = 'noopener';
    abrir.setAttribute('aria-label', 'Abrir a declaração ' + d.codigo);
    acoes.appendChild(abrir);
    caixa.appendChild(acoes);
    caixa.acoes = acoes;
    return caixa;
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.declaracoes = {
    SITUACAO: SITUACAO, cartao: cartao, data: data, cnpj: cnpj, enderecoPublico: enderecoPublico
  };
})(window);
