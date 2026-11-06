/* Perfil do morador, do porteiro e do síndico — a mesma tela nos três
   papéis (antes, uma cópia inteira em cada página). Carrega o próprio
   cadastro de GET /auth/eu e grava o que o sistema deixa o usuário mudar —
   nome, telefone e data de nascimento — em PATCH /usuarios/eu. A senha vai
   por POST /auth/senha/trocar. */
(function(global) {
  'use strict';
  var formato = global.SmartCondo.formato;

  function montar(papel) {
    var api = global.SmartCondo.api;
    var usuario = api.protegerPagina(papel);
    if (!usuario) return;

    function campo(id) { return document.getElementById(id); }
    var perfil = null;
    var dadosOriginais = null;

    var ROTULO_OCUPACAO = {
      proprietario: 'Proprietário', inquilino: 'Inquilino', coabitante: 'Coabitante'
    };

    function mostrar(id, texto) {
      var el = campo('val-' + id);
      if (!el) return;
      var badge = el.querySelector('.b-txt');
      if (badge) badge.textContent = texto || '—';
      else el.textContent = texto || '—';
    }
    function mesAno(iso) {
      var d = new Date(iso);
      if (isNaN(d)) return '';
      var meses = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                   'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
      return meses[d.getMonth()] + ' de ' + d.getFullYear();
    }

    function pintar(p) {
      perfil = p;
      campo('viewNome').textContent = p.nome;
      var nomeTopo = document.getElementById('hdrName');
      if (nomeTopo) nomeTopo.textContent = p.nome;

      mostrar('nome', p.nome);
      mostrar('cpf', formato.cpf(p.cpf));
      mostrar('nasc', p.data_nascimento ? formato.data(p.data_nascimento) : 'Não informada');
      mostrar('email', p.email);
      mostrar('tel', formato.telefone(p.telefone));
      mostrar('desde', mesAno(p.criado_em));

      if (campo('val-apto')) {
        mostrar('apto', p.unidade ? p.unidade.numero : '—');
        mostrar('bloco', p.unidade && p.unidade.bloco && p.unidade.bloco !== 'unico'
          ? p.unidade.bloco : 'Único');
        mostrar('andar', p.unidade && p.unidade.andar ? p.unidade.andar + 'º andar' : '—');
        mostrar('ocupacao', ROTULO_OCUPACAO[p.tipo_ocupacao] || '—');
        mostrar('vagas', p.unidade ? String(p.unidade.vagas_garagem) : '—');
      }

      campo('edit-nome').value = p.nome;
      campo('edit-tel').value = formato.telefone(p.telefone);
      campo('edit-nasc').value = p.data_nascimento ? String(p.data_nascimento).slice(0, 10) : '';

      var sub = campo('tituloSub');
      if (sub) {
        sub.textContent = (p.unidade ? 'Apto ' + p.unidade.numero + ' — ' : '') + p.nome;
      }

      var etiqueta = document.querySelector('.p-tag');
      if (etiqueta) {
        etiqueta.textContent = (p.unidade ? 'Apto ' + p.unidade.numero : '') || '';
        api.get('/condominios/meu')
          .then(function(c) {
            etiqueta.textContent = c.nome + (p.unidade ? ' · Apto ' + p.unidade.numero : '');
          })
          .catch(function() {});
      }
      fotoPerfil.mostrar(p.foto_url);
    }

    function entrarEdicao() {
      avisar('');
      dadosOriginais = {};
      document.querySelectorAll('.p-edit input, .p-edit select').forEach(function(inp) {
        dadosOriginais[inp.id] = inp.value;
      });
      document.querySelectorAll('.p-card').forEach(function(c) { c.classList.add('edit-mode'); });
      campo('viewActions').style.display = 'none';
      campo('editActions').style.display = 'flex';
    }

    function sairEdicao() {
      document.querySelectorAll('.p-card').forEach(function(c) { c.classList.remove('edit-mode'); });
      campo('viewActions').style.display = 'flex';
      campo('editActions').style.display = 'none';
      dadosOriginais = null;
    }

    function cancelarEdicao() {
      if (dadosOriginais) {
        document.querySelectorAll('.p-edit input, .p-edit select').forEach(function(inp) {
          if (dadosOriginais[inp.id] !== undefined) inp.value = dadosOriginais[inp.id];
        });
      }
      sairEdicao();
    }

    // O resultado de salvar, ou o erro de carregar, aparece logo acima dos
    // botões (antes chamava um aviso flutuante que já não existia).
    function avisar(texto, sucesso) {
      var el = campo('avisoPerfil');
      el.className = 'form-erro' + (sucesso ? ' sucesso' : '');
      el.textContent = texto;
    }

    function salvarDados() {
      var nome = campo('edit-nome').value.trim();
      if (nome.length < 3) {
        avisar('O nome precisa ter pelo menos 3 caracteres.');
        return;
      }
      var corpo = { nome: nome, telefone: campo('edit-tel').value };
      // Data em branco significa "não informada"; a API aceita nulo.
      corpo.data_nascimento = campo('edit-nasc').value || null;

      var botao = campo('editActions').querySelector('button');
      if (botao) botao.disabled = true;

      api.patch('/usuarios/eu', corpo)
        .then(function(p) {
          pintar(p);
          // A sessão guarda o nome que aparece no topo das outras telas.
          api.sessao.abrir(api.sessao.token(), p);
          sairEdicao();
          avisar('Perfil atualizado: suas alterações foram salvas.', true);
        })
        .catch(function(e) { avisar(e.message); })
        .then(function() { if (botao) botao.disabled = false; });
    }

    campo('formSenha').addEventListener('submit', function(evento) {
      evento.preventDefault();
      var erro = campo('erroSenha');
      erro.className = 'form-erro';
      erro.textContent = '';

      var atual = campo('senhaAtual').value;
      var nova = campo('senhaNova').value;
      var confirma = campo('senhaConfirma').value;
      if (!atual || !nova) {
        erro.textContent = 'Informe a senha atual e a nova senha.';
        return;
      }
      if (nova.length < 8) {
        erro.textContent = 'A nova senha precisa ter pelo menos 8 caracteres.';
        return;
      }
      if (nova !== confirma) {
        erro.textContent = 'A confirmação não confere com a nova senha.';
        return;
      }

      var botao = this.querySelector('button[type=submit]');
      botao.disabled = true;
      api.post('/auth/senha/trocar', { senha_atual: atual, nova_senha: nova })
        .then(function(r) {
          // As outras sessões foram encerradas; esta segue com o token novo.
          api.sessao.abrir(r.access_token, api.sessao.usuario());
          campo('formSenha').reset();
          erro.className = 'form-erro sucesso';
          erro.textContent = r.detalhe;
        })
        .catch(function(e) { erro.textContent = e.message; })
        .then(function() { botao.disabled = false; });
    });

    window.entrarEdicao = entrarEdicao;
    window.salvarDados = salvarDados;
    window.cancelarEdicao = cancelarEdicao;

    api.get('/auth/eu')
      .then(pintar)
      .catch(function(e) { avisar('Não foi possível carregar o perfil: ' + e.message); });
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.perfil = { montar: montar };
})(window);
