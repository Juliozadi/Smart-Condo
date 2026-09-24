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

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.ui = {
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
