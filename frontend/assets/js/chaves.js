/* Quadro de chaves (portaria e síndico): quem levou cada chave, quando,
   quem entregou e quem recebeu de volta. A chave de apartamento só sai
   para quem mora lá ou para quem o morador autorizou — a tela mostra só
   essas pessoas, e para a autorizada pede o CPF do documento apresentado. */
(function(global) {
  'use strict';

  function el(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function quando(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + ' às ' +
      d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }).replace(':', 'h');
  }
  function botao(texto, rotulo, classe) {
    var b = el('button', 'contato-btn' + (classe ? ' ' + classe : ''), texto);
    b.type = 'button';
    b.setAttribute('aria-label', rotulo);
    return b;
  }
  function grupo(rotulo, id, tipo) {
    var g = el('div', 'form-group');
    var l = el('label', null, rotulo);
    l.htmlFor = id;
    var i = el('input');
    i.id = id;
    i.type = tipo || 'text';
    g.appendChild(l);
    g.appendChild(i);
    return { caixa: g, entrada: i };
  }

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    function campo(id) { return document.getElementById(id); }

    function formRetirada(c, caixa) {
      var form = el('form', 'chave-retirada');
      form.noValidate = true;
      var erro = el('p', 'form-erro');
      erro.setAttribute('role', 'alert');
      var enviar = el('button', 'action-btn compacto', 'Entregar a chave');
      enviar.type = 'submit';
      var coletar;

      if (!c.unidade_id) {
        var nome = grupo('Quem está levando', 'rNome' + c.id);
        nome.entrada.maxLength = 160;
        nome.entrada.required = true;
        var doc = grupo('Documento (opcional)', 'rDoc' + c.id);
        doc.entrada.maxLength = 20;
        form.appendChild(nome.caixa);
        form.appendChild(doc.caixa);
        coletar = function() {
          var corpo = { nome: nome.entrada.value.trim(), documento: doc.entrada.value.trim() || null };
          if (corpo.nome.length < 3) return 'Informe quem está levando a chave.';
          return corpo;
        };
      } else {
        var lista = el('fieldset', 'chave-quem');
        lista.appendChild(el('legend', null, 'Quem pode levar a chave do apartamento hoje'));
        lista.appendChild(el('p', 'estado-lista', 'Carregando…'));
        var cpf = grupo('CPF do documento apresentado', 'rCpf' + c.id);
        cpf.entrada.inputMode = 'numeric';
        cpf.entrada.autocomplete = 'off';
        cpf.caixa.hidden = true;
        if (global.mascaraCPF) global.mascaraCPF(cpf.entrada);
        form.appendChild(lista);
        form.appendChild(cpf.caixa);
        api.get('/chaves/' + c.id + '/quem-pode-retirar').then(function(pessoas) {
          lista.querySelector('.estado-lista').remove();
          if (!pessoas.length) {
            lista.appendChild(el('p', 'regras-aviso',
              'Ninguém pode levar esta chave hoje. O morador autoriza pelo SmartCondo, em ' +
              'Visitantes Autorizados, marcando "pode retirar a chave".'));
            enviar.disabled = true;
            return;
          }
          pessoas.forEach(function(p, i) {
            var rotulo = el('label', 'permissao-item');
            var radio = el('input');
            radio.type = 'radio';
            radio.name = 'quem' + c.id;
            radio.id = 'quem' + c.id + '_' + i;
            radio.value = p.tipo + ':' + p.id;
            rotulo.htmlFor = radio.id;
            rotulo.appendChild(radio);
            rotulo.appendChild(document.createTextNode(' ' + p.nome + (p.tipo === 'morador'
              ? ' (mora no apartamento)'
              : ' (' + (p.detalhe || 'autorizada') + (p.documento ? ', CPF ' + p.documento : '') + ')')));
            radio.addEventListener('change', function() {
              cpf.caixa.hidden = p.tipo !== 'autorizacao';
              if (!cpf.caixa.hidden) cpf.entrada.focus();
            });
            lista.appendChild(rotulo);
          });
        }).catch(function(e) { lista.textContent = e.message; });
        coletar = function() {
          var marcado = form.querySelector('input[type=radio]:checked');
          if (!marcado) return 'Escolha quem está levando a chave.';
          var partes = marcado.value.split(':');
          if (partes[0] === 'morador') return { morador_id: +partes[1] };
          var documento = cpf.entrada.value.replace(/\D/g, '');
          if (documento.length !== 11) return 'Digite o CPF do documento que a pessoa apresentou.';
          return { autorizacao_id: +partes[1], documento: documento };
        };
      }

      var obs = grupo('Observação (opcional)', 'rObs' + c.id);
      obs.entrada.maxLength = 300;
      form.appendChild(obs.caixa);
      form.appendChild(erro);
      form.appendChild(enviar);
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        erro.textContent = '';
        var corpo = coletar();
        if (typeof corpo === 'string') { erro.textContent = corpo; return; }
        corpo.observacao = obs.entrada.value.trim() || null;
        enviar.disabled = true;
        api.post('/chaves/' + c.id + '/retirada', corpo)
          .then(carregar)
          .catch(function(e) { erro.textContent = e.message; enviar.disabled = false; });
      });
      caixa.appendChild(form);
      return form;
    }

    function historico(c, caixa) {
      if (caixa.hidden === false) { caixa.hidden = true; return; }
      caixa.hidden = false;
      caixa.textContent = 'Carregando…';
      api.get('/chaves/' + c.id + '/movimentacoes').then(function(lista) {
        caixa.innerHTML = '';
        if (!lista.length) { caixa.textContent = 'A chave ainda não saiu da portaria.'; return; }
        var ul = el('ul', 'plano-historico-lista');
        lista.forEach(function(m) {
          var texto = quando(m.retirada_em) + ' — ' + m.retirada_por_nome +
            (m.retirada_por_documento ? ' (' + m.retirada_por_documento + ')' : '') +
            (m.retirada_registrada_por_nome ? ' · entregue por ' + m.retirada_registrada_por_nome : '');
          var li = el('li', null, texto);
          li.appendChild(el('span', 'plano-historico-obs', m.devolvida_em
            ? 'Devolvida em ' + quando(m.devolvida_em) +
              (m.devolucao_registrada_por_nome ? ', recebida por ' + m.devolucao_registrada_por_nome : '')
            : 'Ainda fora da portaria'));
          if (m.observacao) li.appendChild(el('span', 'plano-historico-obs', m.observacao));
          ul.appendChild(li);
        });
        caixa.appendChild(ul);
      }).catch(function(e) { caixa.textContent = e.message; });
    }

    function cartao(c) {
      var caixa = el('article', 'form-card chave' + (c.na_portaria ? '' : ' fora'));
      caixa.setAttribute('aria-label', 'Chave ' + c.nome);
      var topo = el('div', 'assembleia-topo');
      topo.appendChild(el('h3', null, c.nome));
      topo.appendChild(el('span', 'badge ' + (c.na_portaria ? 'badge-ok' : 'badge-pending'),
        c.na_portaria ? 'Na portaria' : 'Fora'));
      caixa.appendChild(topo);
      var partes = [];
      if (c.unidade) partes.push('Do apto ' + c.unidade);
      if (c.posicao) partes.push('Quadro ' + c.posicao);
      if (c.unidade) partes.push('só sai para quem mora lá ou para quem o morador autorizou');
      if (partes.length) caixa.appendChild(el('p', 'assembleia-periodo', partes.join(' · ')));
      if (!c.na_portaria) {
        caixa.appendChild(el('p', 'chave-com', 'Com ' + c.com + ' desde ' + quando(c.retirada_em)));
      }
      if (c.observacao) caixa.appendChild(el('p', 'plano-obs', c.observacao));

      var acoes = el('div', 'infracao-acoes');
      var form = null;
      if (c.na_portaria) {
        var bEntregar = botao('Entregar', 'Entregar a chave ' + c.nome);
        bEntregar.addEventListener('click', function() {
          if (!form) form = formRetirada(c, caixa);
          else form.hidden = !form.hidden;
          var primeiro = form.querySelector('input');
          if (primeiro && !form.hidden) primeiro.focus();
        });
        acoes.appendChild(bEntregar);
      } else {
        var bVoltou = botao('Recebi de volta', 'Recebi de volta a chave ' + c.nome);
        bVoltou.addEventListener('click', function() {
          bVoltou.disabled = true;
          api.post('/chaves/' + c.id + '/devolucao', {})
            .then(carregar)
            .catch(function(e) { bVoltou.disabled = false; alert(e.message); });
        });
        acoes.appendChild(bVoltou);
      }
      var bHistorico = botao('Histórico', 'Histórico da chave ' + c.nome);
      var bRemover = botao('Remover', 'Remover a chave ' + c.nome, 'perigo-texto');
      acoes.appendChild(bHistorico);
      acoes.appendChild(bRemover);
      caixa.appendChild(acoes);
      var hist = el('div', 'plano-historico');
      hist.hidden = true;
      caixa.appendChild(hist);
      bHistorico.addEventListener('click', function() { historico(c, hist); });
      bRemover.addEventListener('click', function() {
        if (!confirm('Tirar a chave "' + c.nome + '" do quadro? O histórico fica guardado.')) return;
        bRemover.disabled = true;
        api.remover('/chaves/' + c.id)
          .then(carregar)
          .catch(function(e) { bRemover.disabled = false; alert(e.message); });
      });
      return caixa;
    }

    function carregar() {
      return api.get('/chaves').then(function(lista) {
        var caixa = campo('listaChaves');
        caixa.innerHTML = '';
        var fora = lista.filter(function(c) { return !c.na_portaria; }).length;
        campo('totPortaria').textContent = lista.length - fora;
        campo('totFora').textContent = fora;
        lista.forEach(function(c) { caixa.appendChild(cartao(c)); });
        campo('estadoChaves').textContent = lista.length ? ''
          : 'Nenhuma chave no quadro. Cadastre abaixo as chaves que a portaria guarda.';
      }).catch(function(e) { campo('estadoChaves').textContent = e.message; });
    }

    api.get('/condominios/meu/unidades').then(function(unidades) {
      var sel = campo('cUnidade');
      unidades.forEach(function(u) {
        var op = document.createElement('option');
        op.value = u.id;
        op.textContent = 'Apto ' + u.numero + (u.bloco && u.bloco !== 'unico' ? ' — ' + u.bloco : '');
        sel.appendChild(op);
      });
    }).catch(function() {});

    campo('formChave').addEventListener('submit', function(evento) {
      evento.preventDefault();
      var erro = campo('erroChave');
      erro.className = 'form-erro';
      erro.textContent = '';
      var corpo = {
        nome: campo('cNome').value.trim(),
        unidade_id: +campo('cUnidade').value || null,
        posicao: campo('cPosicao').value.trim() || null,
        observacao: campo('cObservacao').value.trim() || null
      };
      if (corpo.nome.length < 3) { erro.textContent = 'Dê um nome à chave.'; return; }
      var enviar = this.querySelector('button[type=submit]');
      enviar.disabled = true;
      api.post('/chaves', corpo).then(function(c) {
        campo('formChave').reset();
        erro.className = 'form-erro sucesso';
        erro.textContent = '"' + c.nome + '" está no quadro.';
        return carregar();
      }).catch(function(e) { erro.textContent = e.message; })
        .then(function() { enviar.disabled = false; });
    });

    campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.chaves = { montar: montar };
})(window);
