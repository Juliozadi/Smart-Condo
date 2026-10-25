/* Advertências e multas: o cartão de cada notificação, igual para o
   síndico e para o morador — o que aconteceu, o artigo, o prazo, a defesa
   e a decisão. Quem chama acrescenta o que é dele: o síndico, os botões
   de decidir; o morador, o formulário da defesa. */
(function(global) {
  'use strict';

  var STATUS = {
    notificada: ['Aguardando defesa', 'badge-pending'],
    defesa_apresentada: ['Defesa em análise', 'badge-blue'],
    confirmada: ['Mantida', 'badge-alert'],
    anulada: ['Anulada', 'badge-neutral']
  };

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function data(iso) { return iso ? iso.slice(0, 10).split('-').reverse().join('/') : ''; }
  function dinheiro(v) {
    return Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }
  function titulo(i, comUnidade) {
    var t = i.tipo === 'multa' ? 'Multa de ' + dinheiro(i.valor) : 'Advertência';
    return (comUnidade ? 'Apto ' + i.unidade + ' — ' : '') + t;
  }

  function cartao(i, comUnidade) {
    var caixa = el('article', 'form-card infracao');
    caixa.setAttribute('aria-label', titulo(i, comUnidade));
    var topo = el('div', 'assembleia-topo');
    topo.appendChild(el('h3', null, titulo(i, comUnidade)));
    var s = STATUS[i.status] || [i.status, 'badge-neutral'];
    topo.appendChild(el('span', 'badge ' + s[1], s[0]));
    caixa.appendChild(topo);

    caixa.appendChild(el('p', 'assembleia-periodo',
      'Ocorrida em ' + data(i.ocorrida_em) + (i.artigo ? ' · ' + i.artigo : '')));
    caixa.appendChild(el('p', 'infracao-descricao', i.descricao));
    if (i.status === 'notificada') {
      caixa.appendChild(el('p', 'infracao-prazo', 'Prazo de defesa: até ' + data(i.prazo_defesa)));
    }
    if (comUnidade && i.reincidencias) {
      caixa.appendChild(el('p', 'infracao-reincidencia',
        i.reincidencias + (i.reincidencias === 1 ? ' outra mantida' : ' outras mantidas') +
        ' para este apartamento nos últimos 12 meses (Código Civil, art. 1.337).'));
    }
    if (i.defesa) {
      var defesa = el('blockquote', 'infracao-defesa');
      defesa.appendChild(el('strong', null, 'Defesa' + (i.defesa_por_nome ? ' de ' + i.defesa_por_nome : '') +
        ', em ' + data(i.defesa_em) + ':'));
      defesa.appendChild(el('span', null, ' ' + i.defesa));
      caixa.appendChild(defesa);
    }
    if (i.decisao_motivo) {
      caixa.appendChild(el('p', 'infracao-decisao',
        (i.status === 'confirmada' ? 'Mantida' : 'Anulada') + ' pelo síndico em ' +
        data(i.decidida_em) + ': ' + i.decisao_motivo +
        (i.cobranca_id ? ' A multa entrou nas cobranças do apartamento.' : '')));
    }
    return caixa;
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.infracoes = { STATUS: STATUS, cartao: cartao, data: data, dinheiro: dinheiro };
})(window);
