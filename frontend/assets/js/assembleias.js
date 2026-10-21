/* Assembleia virtual: o cartão de cada assembleia, igual para síndico e
   morador — pauta, período, quantos apartamentos votaram e, depois de
   encerrada, o resultado. Quem chama acrescenta o que é dele: o síndico,
   o cancelamento; o morador, a cédula. */
(function(global) {
  'use strict';

  var SITUACAO = {
    agendada: ['Agendada', 'badge-blue'], aberta: ['Votação aberta', 'badge-ok'],
    encerrada: ['Encerrada', 'badge-neutral'], cancelada: ['Cancelada', 'badge-alert']
  };
  var MAIORIA = {
    simples: 'maioria simples', dois_tercos: '2/3 dos apartamentos', unanimidade: 'unanimidade'
  };
  var ESCOLHA = { a_favor: 'A favor', contra: 'Contra', abstencao: 'Abstenção' };

  function quando(iso) {
    var d = new Date(iso);
    return ('0' + d.getDate()).slice(-2) + '/' + ('0' + (d.getMonth() + 1)).slice(-2) +
      ' às ' + ('0' + d.getHours()).slice(-2) + 'h' + ('0' + d.getMinutes()).slice(-2);
  }
  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  function cartao(a) {
    var caixa = el('article', 'form-card assembleia');
    caixa.setAttribute('aria-label', a.titulo);

    var topo = el('div', 'assembleia-topo');
    topo.appendChild(el('h3', null, a.titulo));
    var s = SITUACAO[a.situacao] || [a.situacao, 'badge-neutral'];
    topo.appendChild(el('span', 'badge ' + s[1], s[0]));
    caixa.appendChild(topo);

    caixa.appendChild(el('p', 'assembleia-periodo',
      'Votação de ' + quando(a.abre_em) + ' a ' + quando(a.encerra_em) +
      (a.convocada_por_nome ? ' · convocada por ' + a.convocada_por_nome : '')));
    if (a.descricao) caixa.appendChild(el('p', 'assembleia-descricao', a.descricao));
    if (a.situacao === 'cancelada' && a.motivo_cancelamento) {
      caixa.appendChild(el('p', 'form-erro', 'Cancelada: ' + a.motivo_cancelamento));
    }
    if (a.situacao !== 'agendada' && a.situacao !== 'cancelada') {
      caixa.appendChild(el('p', 'assembleia-quorum',
        a.unidades_que_votaram + ' de ' + a.total_unidades +
        (a.total_unidades === 1 ? ' apartamento votou' : ' apartamentos votaram') +
        (a.situacao === 'aberta' ? ' até agora. O resultado aparece quando a votação encerrar.' : '.')));
    }

    var pauta = el('ol', 'assembleia-pauta');
    a.itens.forEach(function(item) {
      var li = el('li');
      li.appendChild(el('strong', null, item.titulo));
      li.appendChild(el('span', 'assembleia-maioria', ' — ' + (MAIORIA[item.maioria] || item.maioria)));
      if (item.descricao) li.appendChild(el('p', 'assembleia-descricao', item.descricao));
      if (item.meu_voto) {
        li.appendChild(el('p', 'assembleia-meu-voto', 'Voto do seu apartamento: ' + ESCOLHA[item.meu_voto]));
      }
      if (item.resultado) {
        var r = item.resultado;
        var linha = el('p', 'assembleia-resultado');
        linha.appendChild(el('span', 'badge ' + (r.aprovado ? 'badge-ok' : 'badge-alert'),
                             r.aprovado ? 'Aprovado' : 'Não aprovado'));
        linha.appendChild(document.createTextNode(
          ' A favor ' + r.a_favor + ' · Contra ' + r.contra + ' · Abstenção ' + r.abstencao));
        li.appendChild(linha);
      }
      pauta.appendChild(li);
    });
    caixa.appendChild(pauta);
    return caixa;
  }

  global.SmartCondo.assembleias = { cartao: cartao, ESCOLHA: ESCOLHA, MAIORIA: MAIORIA };
})(window);
