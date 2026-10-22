/* Agendamento de mudança: o cartão de cada mudança, igual para morador,
   síndico e portaria — data, horário, empresa e situação. Quem chama
   acrescenta os botões que são dele (cancelar, aprovar, recusar). */
(function(global) {
  'use strict';

  var STATUS = {
    pendente: ['Aguardando o síndico', 'badge-pending'],
    aprovada: ['Aprovada', 'badge-ok'],
    recusada: ['Recusada', 'badge-alert'],
    cancelada: ['Cancelada', 'badge-neutral'],
    concluida: ['Realizada', 'badge-neutral']
  };
  var TIPO = { chegada: 'Chegada ao apartamento', saida: 'Saída do apartamento' };
  var MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  var DIAS = ['', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function hora(t) { return (t || '').slice(0, 5); }
  function horaCurta(t) {
    var h = +t.slice(0, 2), m = t.slice(3, 5);
    return h + 'h' + (m === '00' ? '' : m);
  }
  // "2026-10-23" → dia da semana de 1 (segunda) a 7 (domingo), sem fuso.
  function diaDaSemana(iso) {
    var p = iso.split('-');
    var d = new Date(+p[0], +p[1] - 1, +p[2]).getDay();
    return d === 0 ? 7 : d;
  }
  function dataIso(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' +
      ('0' + d.getDate()).slice(-2);
  }
  function somarDias(dias) {
    var d = new Date();
    d.setDate(d.getDate() + dias);
    return dataIso(d);
  }

  /* As regras da API em frases: "Segunda a sexta, das 8h às 18h". */
  function frasesDasRegras(regras) {
    var frases = ['Peça com pelo menos ' + regras.antecedencia_minima_dias +
                  ' dias de antecedência; o síndico aprova ou recusa.'];
    var grupos = [];
    for (var dia = 1; dia <= 7; dia++) {
      var h = regras.horarios[dia];
      var chave = h ? hora(h.inicio) + '-' + hora(h.fim) : 'nao';
      var ultimo = grupos[grupos.length - 1];
      if (ultimo && ultimo.chave === chave) ultimo.fim = dia;
      else grupos.push({ chave: chave, inicio: dia, fim: dia, h: h });
    }
    grupos.forEach(function(g) {
      var dias = g.inicio === g.fim ? DIAS[g.inicio]
        : DIAS[g.inicio] + ' a ' + DIAS[g.fim].toLowerCase();
      frases.push(g.h ? dias + ', das ' + horaCurta(g.h.inicio) + ' às ' + horaCurta(g.h.fim) + '.'
                      : dias + ', não há mudança.');
    });
    frases.push('Uma mudança de cada vez: o elevador de serviço é um só.');
    return frases;
  }

  function cartao(m, comUnidade) {
    var card = el('article', 'reserve-card mudanca');
    card.setAttribute('aria-label', 'Mudança de ' + m.data.split('-').reverse().join('/'));
    var p = m.data.split('-');
    var data = el('div', 'reserve-date' + (m.status === 'pendente' ? ' pendente' : ''));
    data.appendChild(el('div', 'day', p[2]));
    data.appendChild(el('div', 'month', MESES[+p[1] - 1]));

    var info = el('div', 'reserve-info');
    info.appendChild(el('h3', null,
      (comUnidade ? 'Apto ' + m.unidade + ' — ' : '') + TIPO[m.tipo]));
    info.appendChild(el('p', null,
      DIAS[diaDaSemana(m.data)] + ', ' + hora(m.hora_inicio) + ' – ' + hora(m.hora_fim) +
      (m.empresa ? ' · ' + m.empresa : '')));
    if (comUnidade && m.solicitada_por_nome) {
      info.appendChild(el('p', 'comunicado-autor', 'Pedido por ' + m.solicitada_por_nome));
    }
    if (m.observacao) info.appendChild(el('p', 'mudanca-obs', m.observacao));
    if (m.status === 'recusada' && m.motivo_recusa) {
      info.appendChild(el('p', 'mudanca-motivo', 'Motivo da recusa: ' + m.motivo_recusa));
    }
    if (m.status === 'cancelada' && m.cancelada_pelo_sindico) {
      info.appendChild(el('p', 'mudanca-motivo',
        'Cancelada pelo síndico' + (m.motivo_cancelamento ? ': ' + m.motivo_cancelamento : '.')));
    }
    var s = STATUS[m.status] || [m.status, 'badge-neutral'];
    var lado = el('div', 'mudanca-lado');
    lado.appendChild(el('span', 'badge ' + s[1], s[0]));

    card.appendChild(data);
    card.appendChild(info);
    card.appendChild(lado);
    card.acoes = lado;
    return card;
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.mudancas = {
    STATUS: STATUS, TIPO: TIPO, cartao: cartao, frasesDasRegras: frasesDasRegras,
    diaDaSemana: diaDaSemana, somarDias: somarDias, hora: hora, horaCurta: horaCurta
  };
})(window);
