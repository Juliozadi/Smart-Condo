/* Animais de estimação: o morador cadastra os do apartamento; o síndico vê
   todos, cadastra por qualquer apartamento e lembra quem está com a vacina
   antirrábica vencida ou sem registro; a portaria consulta, com busca, para
   saber de quem é o animal solto na garagem. */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;
  var el = formato.el, botao = formato.botao, data = formato.data;

  var ESPECIE = { cao: 'Cachorro', gato: 'Gato', ave: 'Ave', outro: 'Outro' };
  var PORTE = { pequeno: 'pequeno', medio: 'médio', grande: 'grande' };

  function vacina(a) {
    if (a.vacina === 'em_dia') return ['Vacina em dia até ' + data(a.vacina_antirrabica_ate), 'badge-ok'];
    if (a.vacina === 'vencida') return ['Vacina vencida em ' + data(a.vacina_antirrabica_ate), 'badge-alert'];
    return ['Vacina sem registro', 'badge-alert'];
  }

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;
    function campo(id) { return document.getElementById(id); }
    var editando = null;
    var todos = [];

    function cartao(a) {
      var caixa = el('article', 'form-card animal vacina-' + a.vacina);
      caixa.setAttribute('aria-label', a.nome + ', apto ' + a.unidade);
      var topo = el('div', 'assembleia-topo');
      topo.appendChild(el('h3', null, a.nome + ' — ' + (ESPECIE[a.especie] || a.especie).toLowerCase() +
        ', porte ' + (PORTE[a.porte] || a.porte)));
      var v = vacina(a);
      topo.appendChild(el('span', 'badge ' + v[1], v[0]));
      caixa.appendChild(topo);
      var partes = ['Apto ' + a.unidade];
      if (a.raca) partes.push(a.raca);
      if (a.cor) partes.push(a.cor);
      caixa.appendChild(el('p', 'assembleia-periodo', partes.join(' · ')));
      if (a.observacao) caixa.appendChild(el('p', 'chave-com', a.observacao));
      if (papel !== 'morador' && a.cadastrado_por_nome) {
        caixa.appendChild(el('p', 'plano-obs', 'Cadastrado por ' + a.cadastrado_por_nome));
      }
      if (a.pode_editar) {
        var acoes = el('div', 'infracao-acoes');
        var editar = botao('Editar', 'Editar ' + a.nome);
        editar.addEventListener('click', function() { abrirEdicao(a); });
        var remover = botao('Remover', 'Remover ' + a.nome, 'perigo-texto');
        remover.addEventListener('click', function() {
          if (!confirm('Remover ' + a.nome + ' da lista do apartamento?')) return;
          remover.disabled = true;
          api.remover('/animais/' + a.id).then(carregar)
            .catch(function(e) { remover.disabled = false; alert(e.message); });
        });
        acoes.appendChild(editar);
        acoes.appendChild(remover);
        caixa.appendChild(acoes);
      }
      return caixa;
    }

    function desenhar() {
      var caixa = campo('listaAnimais');
      caixa.innerHTML = '';
      var busca = campo('buscaAnimais') ? formato.semAcento(campo('buscaAnimais').value.trim().toLowerCase()) : '';
      var lista = todos.filter(function(a) {
        if (!busca) return true;
        var texto = formato.semAcento([a.nome, a.raca, a.cor, a.unidade, ESPECIE[a.especie]].join(' ').toLowerCase());
        return texto.indexOf(busca) >= 0;
      });
      lista.forEach(function(a) { caixa.appendChild(cartao(a)); });
      campo('estadoAnimais').textContent = lista.length ? '' :
        (todos.length ? 'Nenhum animal encontrado.' :
          (papel === 'morador' ? 'Nenhum animal cadastrado no seu apartamento.' : 'Nenhum animal cadastrado.'));
    }

    function carregar() {
      var pendentes = campo('soPendentes') && campo('soPendentes').checked;
      return api.get('/animais' + (pendentes ? '?vacina=pendente' : '')).then(function(lista) {
        todos = lista;
        if (campo('totAnimais') && !pendentes) campo('totAnimais').textContent = lista.length;
        if (campo('totPendentes') && !pendentes) {
          campo('totPendentes').textContent = lista.filter(function(a) { return a.vacina !== 'em_dia'; }).length;
        }
        desenhar();
      }).catch(function(e) { campo('estadoAnimais').textContent = e.message; });
    }

    /* ── Cadastro e edição (morador e síndico) ─────────────────── */
    var form = campo('formAnimal');
    function limparForm() {
      editando = null;
      form.reset();
      campo('tituloForm').textContent = 'Cadastrar animal';
      campo('btnSalvarAnimal').textContent = 'Cadastrar';
      campo('btnCancelarEdicao').hidden = true;
      if (campo('anUnidade')) campo('anUnidade').disabled = false;
    }
    function abrirEdicao(a) {
      editando = a;
      campo('anNome').value = a.nome;
      campo('anEspecie').value = a.especie;
      campo('anPorte').value = a.porte;
      campo('anRaca').value = a.raca || '';
      campo('anCor').value = a.cor || '';
      campo('anVacina').value = a.vacina_antirrabica_ate || '';
      campo('anObservacao').value = a.observacao || '';
      if (campo('anUnidade')) { campo('anUnidade').value = a.unidade_id; campo('anUnidade').disabled = true; }
      campo('tituloForm').textContent = 'Editar ' + a.nome;
      campo('btnSalvarAnimal').textContent = 'Salvar alterações';
      campo('btnCancelarEdicao').hidden = false;
      form.scrollIntoView({ behavior: 'smooth', block: 'start' });
      campo('anNome').focus();
    }
    if (form) {
      campo('anVacina').max = formato.hojeIso(400);
      campo('btnCancelarEdicao').addEventListener('click', limparForm);
      form.addEventListener('submit', function(evento) {
        evento.preventDefault();
        var erro = campo('erroAnimal');
        erro.className = 'form-erro';
        erro.textContent = '';
        var corpo = {
          nome: campo('anNome').value.trim(),
          especie: campo('anEspecie').value,
          porte: campo('anPorte').value,
          raca: campo('anRaca').value.trim() || null,
          cor: campo('anCor').value.trim() || null,
          vacina_antirrabica_ate: campo('anVacina').value || null,
          observacao: campo('anObservacao').value.trim() || null
        };
        if (!corpo.nome) { erro.textContent = 'Informe o nome do animal.'; return; }
        if (!corpo.especie || !corpo.porte) { erro.textContent = 'Escolha a espécie e o porte.'; return; }
        if (!editando && campo('anUnidade')) {
          corpo.unidade_id = +campo('anUnidade').value || null;
          if (!corpo.unidade_id) { erro.textContent = 'Escolha o apartamento.'; return; }
        }
        var b = campo('btnSalvarAnimal');
        b.disabled = true;
        var pedido = editando ? api.put('/animais/' + editando.id, corpo) : api.post('/animais', corpo);
        pedido.then(function(a) {
          var eraEdicao = !!editando;
          limparForm();
          // A mensagem só depois da lista nova: quem lê o aviso já vê o
          // animal atualizado.
          return carregar().then(function() {
            erro.className = 'form-erro sucesso';
            erro.textContent = eraEdicao ? 'Cadastro de ' + a.nome + ' atualizado.' : a.nome + ' cadastrado.';
          });
        }).catch(function(e) { erro.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }

    if (campo('anUnidade')) {
      api.get('/condominios/meu/unidades').then(function(unidades) {
        unidades.forEach(function(u) {
          var op = document.createElement('option');
          op.value = u.id;
          op.textContent = 'Apto ' + (u.bloco && u.bloco !== 'unico' ? u.bloco + ' ' : '') + u.numero;
          campo('anUnidade').appendChild(op);
        });
      }).catch(function() {});
    }

    if (campo('btnLembrete')) {
      campo('btnLembrete').addEventListener('click', function() {
        var b = this;
        var aviso = campo('avisoLembrete');
        b.disabled = true;
        aviso.className = 'form-erro';
        api.post('/animais/lembrete-vacina', {}).then(function(r) {
          aviso.className = 'form-erro sucesso';
          aviso.textContent = r.animais
            ? 'Lembrete enviado a ' + r.apartamentos + (r.apartamentos === 1 ? ' apartamento' : ' apartamentos') +
              ' (' + r.animais + (r.animais === 1 ? ' animal' : ' animais') + ').'
            : 'Nenhum lembrete a enviar: quem está pendente já foi lembrado nesta semana.';
          return carregar();
        }).catch(function(e) { aviso.textContent = e.message; })
          .then(function() { b.disabled = false; });
      });
    }
    if (campo('soPendentes')) campo('soPendentes').addEventListener('change', carregar);
    if (campo('buscaAnimais')) campo('buscaAnimais').addEventListener('input', desenhar);
    if (campo('hdrName')) campo('hdrName').textContent = usuario.nome;
    carregar();
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.animais = { montar: montar };
})(window);
