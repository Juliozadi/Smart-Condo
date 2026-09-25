/* ═══════════════════════════════════════════════════════════════
   SmartCondo — apoio às telas de administração

   Peças repetidas entre as listagens com CRUD: o modal de formulário,
   a limpeza da tabela, formatações e o atraso da busca enquanto se digita.
   Carregue depois de api.js.
   ═══════════════════════════════════════════════════════════════ */
(function(global) {
  'use strict';

  /* Remove as linhas da tabela, preservando o cabeçalho. */
  function limparTabela(tabela) {
    var cabecalho = tabela.querySelector('.table-head');
    tabela.innerHTML = '';
    if (cabecalho) tabela.appendChild(cabecalho);
  }

  /* Adia a chamada enquanto o usuário ainda digita. */
  function aguardar(fn, ms) {
    var timer = null;
    return function() {
      var args = arguments, contexto = this;
      clearTimeout(timer);
      timer = setTimeout(function() { fn.apply(contexto, args); }, ms || 300);
    };
  }

  /* Compara texto ignorando acentos: quem digita "convencao" espera
     encontrar "Convenção". */
  function semAcento(texto) {
    return (texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function formatarCnpj(valor) {
    var d = (valor || '').replace(/\D/g, '');
    if (d.length !== 14) return valor || '';
    return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5, 8) +
           '/' + d.slice(8, 12) + '-' + d.slice(12);
  }

  function formatarCpf(valor) {
    var d = (valor || '').replace(/\D/g, '');
    if (d.length !== 11) return valor || '';
    return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
  }

  function formatarTelefone(valor) {
    var d = (valor || '').replace(/\D/g, '');
    if (d.length === 11) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
    if (d.length === 10) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 6) + '-' + d.slice(6);
    return valor || '';
  }

  var ROTULO_PAPEL = {
    admin: 'Administrador', sindico: 'Síndico',
    porteiro: 'Porteiro', morador: 'Morador'
  };

  var ROTULO_STATUS = {
    ativo: 'Ativo',
    aguardando_codigo: 'Aguardando código',
    aguardando_aprovacao: 'Aguardando aprovação',
    recusado: 'Recusado',
    inativo: 'Inativo'
  };

  var CLASSE_STATUS = {
    ativo: 'badge-ok',
    aguardando_codigo: 'badge-pending',
    aguardando_aprovacao: 'badge-pending',
    recusado: 'badge-alert',
    inativo: 'badge-neutral'
  };

  /* Monta o controlador de um modal de formulário. */
  function modal(idModal, idForm, idErro) {
    var fundo = document.getElementById(idModal);
    var form = document.getElementById(idForm);
    var caixaErro = document.getElementById(idErro);
    var ultimoFoco = null;

    var soltarFoco = null;

    function abrir() {
      ultimoFoco = document.activeElement;
      fundo.classList.add('aberto');
      if (soltarFoco) soltarFoco();
      soltarFoco = global.SmartCondo.api.prenderFoco(fundo);
      var primeiro = form.querySelector('input, select, textarea');
      if (primeiro) primeiro.focus();
    }

    function fechar() {
      if (soltarFoco) { soltarFoco(); soltarFoco = null; }
      fundo.classList.remove('aberto');
      if (ultimoFoco && ultimoFoco.focus) ultimoFoco.focus();
    }

    function limpar() {
      form.reset();
      erro('');
      form.querySelectorAll('.erro-validacao').forEach(function(el) { el.remove(); });
    }

    function erro(mensagem) {
      if (caixaErro) caixaErro.textContent = mensagem || '';
    }

    // Clicar fora e Esc fecham, como se espera de um diálogo.
    fundo.addEventListener('click', function(e) {
      if (e.target === fundo) fechar();
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && fundo.classList.contains('aberto')) fechar();
    });

    var cancelar = document.getElementById('btnCancelar');
    if (cancelar) cancelar.addEventListener('click', fechar);

    /* montarEnvio devolve a promessa da chamada, ou null para abortar. */
    function aoEnviar(montarEnvio, aoConcluir) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        erro('');

        var botao = form.querySelector('button[type=submit]');
        var textoOriginal = botao.innerHTML;

        var envio;
        try {
          envio = montarEnvio();
        } catch (falha) {
          erro(falha.message);
          return;
        }
        if (!envio) return;

        botao.disabled = true;
        botao.innerHTML = 'Salvando...';

        envio
          .then(function(resposta) {
            botao.disabled = false;
            botao.innerHTML = textoOriginal;
            aoConcluir(resposta);
          })
          .catch(function(falha) {
            botao.disabled = false;
            botao.innerHTML = textoOriginal;
            erro(falha.message);
          });
      });
    }

    return { abrir: abrir, fechar: fechar, limpar: limpar, erro: erro, aoEnviar: aoEnviar };
  }

  /* "Editado por Fulano em 25/09/2026 14:32" — quem fez a última alteração
     de um registro (pedido do grupo: com vários administradores, cada
     mudança precisa mostrar o autor). */
  function dataHora(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var dois = function(n) { return ('0' + n).slice(-2); };
    return dois(d.getDate()) + '/' + dois(d.getMonth() + 1) + '/' + d.getFullYear() +
      ' ' + dois(d.getHours()) + ':' + dois(d.getMinutes());
  }
  function textoAlteracao(r) {
    if (!r) return '';
    return r.rotulo + ' por ' + (r.autor_nome || 'sistema') + ' em ' + dataHora(r.feito_em);
  }

  /* Preenche a lista de histórico da janela de edição. */
  function mostrarHistorico(lista, entidade, id) {
    lista.textContent = '';
    var carregando = document.createElement('li');
    carregando.textContent = 'Carregando…';
    lista.appendChild(carregando);
    return global.SmartCondo.api
      .get('/admin/historico?entidade=' + entidade + '&entidade_id=' + id)
      .then(function(registros) {
        lista.textContent = '';
        if (!registros.length) {
          var vazio = document.createElement('li');
          vazio.textContent = 'Nenhuma alteração registrada.';
          lista.appendChild(vazio);
        }
        registros.forEach(function(r) {
          var item = document.createElement('li');
          var quem = document.createElement('strong');
          quem.textContent = textoAlteracao(r);
          item.appendChild(quem);
          if (r.descricao) {
            var oque = document.createElement('span');
            oque.textContent = ' — ' + r.descricao;
            item.appendChild(oque);
          }
          lista.appendChild(item);
        });
      })
      .catch(function(e) { lista.textContent = e.message; });
  }

  /* Inativa um morador ou porteiro que saiu do condomínio: o acesso acaba
     na hora e o histórico fica. Pede confirmação dizendo o que acontece. */
  function inativarUsuario(u, botao, aoConcluir) {
    var efeitos = u.papel === 'morador'
      ? 'O acesso dele termina agora e as reservas futuras são canceladas, liberando os espaços.'
      : 'O acesso dele termina agora.';
    if (!confirm('Inativar ' + u.nome + '?\n\n' + efeitos +
                 ' O histórico (portaria, reservas, pagamentos) é mantido.')) return;
    if (botao) botao.disabled = true;
    global.SmartCondo.api.remover('/usuarios/' + u.id)
      .then(aoConcluir)
      .catch(function(e) { if (botao) botao.disabled = false; alert(e.message); });
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.ui = {
    inativarUsuario: inativarUsuario,
    textoAlteracao: textoAlteracao,
    mostrarHistorico: mostrarHistorico,
    limparTabela: limparTabela,
    aguardar: aguardar,
    semAcento: semAcento,
    formatarCnpj: formatarCnpj,
    formatarCpf: formatarCpf,
    formatarTelefone: formatarTelefone,
    ROTULO_PAPEL: ROTULO_PAPEL,
    ROTULO_STATUS: ROTULO_STATUS,
    CLASSE_STATUS: CLASSE_STATUS,
    modal: modal
  };
})(window);
