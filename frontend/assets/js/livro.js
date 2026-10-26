/* Livro da portaria: a passagem de turno, igual para o porteiro e para o
   síndico. Quem sai anota o que o próximo precisa saber; a anotação
   importante pede a ciência de quem chega e mostra quem já leu. Nada se
   apaga nem se edita: corrige-se com outra anotação, como no livro de
   papel. */
(function(global) {
  'use strict';

  var PAPEL = { porteiro: 'Porteiro', sindico: 'Síndico' };

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

  function cartao(a, darCiencia) {
    var caixa = el('article', 'form-card anotacao' + (a.importante ? ' importante' : ''));
    var autor = a.autor_nome || 'Cadastro removido';
    caixa.setAttribute('aria-label', 'Anotação de ' + autor + ', ' + quando(a.criado_em));
    var topo = el('div', 'assembleia-topo');
    topo.appendChild(el('h3', null, autor + (a.autor_papel ? ' · ' + (PAPEL[a.autor_papel] || '') : '')));
    if (a.importante) topo.appendChild(el('span', 'badge badge-alert', 'Importante'));
    caixa.appendChild(topo);
    caixa.appendChild(el('p', 'assembleia-periodo', quando(a.criado_em)));
    caixa.appendChild(el('p', 'anotacao-texto', a.texto));

    if (a.importante) {
      caixa.appendChild(el('p', 'anotacao-cientes', a.cientes.length
        ? 'Ciente: ' + a.cientes.map(function(c) { return c.nome + ' (' + quando(c.em) + ')'; }).join(', ')
        : 'Ninguém deu ciência ainda.'));
    }
    if (a.preciso_ler) {
      var b = el('button', 'action-btn anotacao-ciente', 'Li e estou ciente');
      b.type = 'button';
      b.setAttribute('aria-label', 'Dar ciência da anotação de ' + autor + ', ' + quando(a.criado_em));
      b.addEventListener('click', function() { darCiencia(a, b); });
      caixa.appendChild(b);
    }
    return caixa;
  }

  function montar(usuario) {
    var api = global.SmartCondo.api;
    function campo(id) { return document.getElementById(id); }

    function preencher(lista, idLista, idEstado, vazio) {
      var caixa = campo(idLista);
      caixa.innerHTML = '';
      campo(idEstado).textContent = lista.length ? '' : vazio;
      lista.forEach(function(a) { caixa.appendChild(cartao(a, darCiencia)); });
    }

    function carregar() {
      return api.get('/livro-portaria').then(function(lista) {
        var ler = lista.filter(function(a) { return a.preciso_ler; });
        campo('blocoLer').hidden = !ler.length;
        preencher(ler, 'listaLer', 'estadoLer', '');
        preencher(lista.filter(function(a) { return !a.preciso_ler; }),
                  'listaLivro', 'estadoLivro', 'Nenhuma anotação no livro ainda.');
      }).catch(function(e) { campo('estadoLivro').textContent = e.message; });
    }

    function darCiencia(a, botao) {
      botao.disabled = true;
      api.post('/livro-portaria/' + a.id + '/ciencia', {})
        .then(carregar)
        .catch(function(e) { botao.disabled = false; alert(e.message); });
    }

    campo('formLivro').addEventListener('submit', function(evento) {
      evento.preventDefault();
      var erro = campo('erroLivro');
      erro.className = 'form-erro';
      erro.textContent = '';
      var corpo = { texto: campo('lTexto').value.trim(), importante: campo('lImportante').checked };
      if (corpo.texto.length < 3) { erro.textContent = 'Escreva a anotação.'; return; }
      var enviar = this.querySelector('button[type=submit]');
      enviar.disabled = true;
      api.post('/livro-portaria', corpo)
        .then(function() {
          campo('formLivro').reset();
          erro.className = 'form-erro sucesso';
          erro.textContent = corpo.importante
            ? 'Anotado. Quem chegar vai ver e dar ciência.' : 'Anotado no livro.';
          return carregar();
        })
        .catch(function(e) { erro.textContent = e.message; })
        .then(function() { enviar.disabled = false; });
    });

    campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.livro = { cartao: cartao, montar: montar };
})(window);
