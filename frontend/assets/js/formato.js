/* Pequenas peças que várias telas usam: criar um elemento com texto (nunca
   innerHTML com dado vindo da API), o botão de ação, e os formatos de
   dinheiro, data, CPF e telefone. Ficam aqui, uma vez só: antes cada tela
   tinha a sua cópia, e algumas já escreviam o mesmo valor de jeitos
   diferentes. Carregado logo depois do api.js. */
(function(global) {
  'use strict';

  function dois(n) { return ('0' + n).slice(-2); }

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function botao(texto, rotulo, classe) {
    var b = el('button', 'contato-btn' + (classe ? ' ' + classe : ''), texto);
    b.type = 'button';
    b.setAttribute('aria-label', rotulo);
    return b;
  }

  // "R$ 1.234,56".
  function dinheiro(valor) {
    return 'R$ ' + Number(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
  }

  // "2026-11-06" (ou o começo de "2026-11-06T14:30:00") vira "06/11/2026".
  // Pelo texto, e não por new Date(): a data sem hora seria lida como
  // meia-noite em UTC e mostraria o dia anterior no Brasil.
  function data(iso) {
    return iso ? String(iso).slice(0, 10).split('-').reverse().join('/') : '';
  }

  // "06/11 às 14h30", no relógio de quem está vendo.
  function quando(iso) {
    var d = new Date(iso);
    return dois(d.getDate()) + '/' + dois(d.getMonth() + 1) + ' às ' +
      dois(d.getHours()) + 'h' + dois(d.getMinutes());
  }

  // A data de hoje (ou daqui a n dias) no formato do <input type="date">.
  function hojeIso(somaDias) {
    var d = new Date();
    d.setDate(d.getDate() + (somaDias || 0));
    return d.getFullYear() + '-' + dois(d.getMonth() + 1) + '-' + dois(d.getDate());
  }

  function cpf(valor) {
    var d = (valor || '').replace(/\D/g, '');
    if (d.length !== 11) return valor || '';
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function telefone(valor) {
    var d = (valor || '').replace(/\D/g, '');
    if (d.length === 11) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
    if (d.length === 10) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 6) + '-' + d.slice(6);
    return valor || '';
  }

  // Para a busca: "João" acha "joao".
  function semAcento(texto) {
    return (texto || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  // "Maria da Silva" vira "MS".
  function iniciais(nome) {
    var p = (nome || '').trim().split(/\s+/);
    return (((p[0] || '')[0] || '') + ((p[p.length - 1] || '')[0] || '')).toUpperCase();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.formato = {
    el: el, botao: botao, dinheiro: dinheiro, data: data, quando: quando, hojeIso: hojeIso,
    cpf: cpf, telefone: telefone, semAcento: semAcento, iniciais: iniciais
  };
})(window);
