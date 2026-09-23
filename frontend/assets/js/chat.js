/* ═══════════════════════════════════════════════════════════════
   SmartCondo — mensagens (chat)
   Documentação, seção 13.5.2: o síndico "pode contatá-los por chat ou
   ligação de voz".

   Carregado pelo sessao.js para síndico, porteiro e morador. Põe um botão
   "Mensagens" na barra superior, com o número de não lidas, e abre um
   painel com os contatos e a conversa. Outras telas abrem uma conversa
   direto com SmartCondo.chat.abrir(id).

   A ligação usa o telefone cadastrado (link tel:): no celular abre a
   discagem, no computador o aplicativo de chamadas configurado.

   Todo texto vindo do servidor entra por textContent — nunca por
   innerHTML —, para que uma mensagem com HTML apareça como texto.
   ═══════════════════════════════════════════════════════════════ */
(function(global) {
  'use strict';

  var api = global.SmartCondo.api;
  var INTERVALO_CONVERSA = 4000, INTERVALO_CONTATOS = 15000, INTERVALO_CONTADOR = 30000;
  var ROTULO = { sindico: 'Síndico', porteiro: 'Porteiro', morador: 'Morador' };

  var painel, fundoEl, lista, conversaEl, mensagensEl, campoTexto, contadorEl, tituloEl, ligarEl, avisoEl, buscaEl;
  var contatos = [], atual = null, ultimoId = 0, timerConversa = null, timerContatos = null;

  function criar(tag, classe, texto) {
    var e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function icone(nome) {
    var i = criar('img'); i.src = api.base + 'assets/img/icons/' + nome + '.svg';
    i.alt = ''; i.width = 16; i.height = 16; return i;
  }
  function hora(iso) {
    var d = new Date(iso), hoje = new Date();
    var hh = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    return d.toDateString() === hoje.toDateString() ? hh : d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + ' ' + hh;
  }
  function telefoneLink(tel) { return 'tel:' + String(tel || '').replace(/[^\d+]/g, ''); }

  /* ── Botão na barra superior ───────────────────────────────── */
  function montarBotao() {
    var destino = document.querySelector('.app-bar-right');
    if (!destino) return;
    var botao = criar('button', 'chat-abrir');
    botao.type = 'button';
    botao.setAttribute('aria-haspopup', 'dialog');
    botao.appendChild(icone('envelope'));
    botao.appendChild(criar('span', 'chat-abrir-texto', 'Mensagens'));
    contadorEl = criar('span', 'chat-contador');
    contadorEl.hidden = true;
    botao.appendChild(contadorEl);
    botao.addEventListener('click', function() { abrirPainel(); });
    destino.insertBefore(botao, destino.firstChild);
    atualizarContador();
    setInterval(atualizarContador, INTERVALO_CONTADOR);
  }

  function atualizarContador() {
    api.get('/mensagens/nao-lidas', { semRedirecionar: true }).then(function(r) {
      if (!contadorEl) return;
      contadorEl.hidden = !r.total;
      contadorEl.textContent = r.total > 99 ? '99+' : String(r.total);
      contadorEl.parentNode.setAttribute('aria-label',
        'Mensagens' + (r.total ? ', ' + r.total + ' não lida' + (r.total > 1 ? 's' : '') : ''));
    }).catch(function() {});
  }

  /* ── Painel ────────────────────────────────────────────────── */
  function montarPainel() {
    painel = criar('div', 'chat-painel');
    painel.setAttribute('role', 'dialog');
    painel.setAttribute('aria-modal', 'true');
    painel.setAttribute('aria-labelledby', 'chatTitulo');
    painel.hidden = true;

    var topo = criar('div', 'chat-topo');
    var voltar = criar('button', 'chat-voltar'); voltar.type = 'button';
    voltar.setAttribute('aria-label', 'Voltar aos contatos'); voltar.appendChild(icone('arrow-left'));
    voltar.addEventListener('click', mostrarContatos);
    tituloEl = criar('h2', 'chat-titulo', 'Mensagens'); tituloEl.id = 'chatTitulo';
    ligarEl = criar('a', 'chat-ligar'); ligarEl.appendChild(icone('phone'));
    ligarEl.appendChild(document.createTextNode('Ligar')); ligarEl.hidden = true;
    var fechar = criar('button', 'chat-fechar'); fechar.type = 'button';
    fechar.setAttribute('aria-label', 'Fechar mensagens'); fechar.appendChild(icone('xmark'));
    fechar.addEventListener('click', fecharPainel);
    topo.appendChild(voltar); topo.appendChild(tituloEl); topo.appendChild(ligarEl); topo.appendChild(fechar);

    avisoEl = criar('p', 'chat-aviso'); avisoEl.setAttribute('role', 'status'); avisoEl.hidden = true;

    lista = criar('div', 'chat-lista');
    buscaEl = criar('input', 'chat-busca');
    buscaEl.type = 'search'; buscaEl.placeholder = 'Buscar pelo nome ou apartamento';
    buscaEl.setAttribute('aria-label', 'Buscar contato');
    buscaEl.addEventListener('input', desenharContatos);
    lista.appendChild(buscaEl);
    lista.appendChild(criar('ul', 'chat-contatos'));

    conversaEl = criar('div', 'chat-conversa'); conversaEl.hidden = true;
    mensagensEl = criar('ol', 'chat-mensagens');
    mensagensEl.setAttribute('aria-live', 'polite');
    var form = criar('form', 'chat-form');
    campoTexto = criar('textarea', 'chat-campo');
    campoTexto.rows = 1; campoTexto.maxLength = 2000;
    campoTexto.placeholder = 'Escreva uma mensagem';
    campoTexto.setAttribute('aria-label', 'Mensagem');
    campoTexto.addEventListener('keydown', function(e) {
      // Enter envia; Shift+Enter quebra a linha.
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit ? form.requestSubmit() : enviar(); }
    });
    var enviarBtn = criar('button', 'chat-enviar', 'Enviar'); enviarBtn.type = 'submit';
    form.appendChild(campoTexto); form.appendChild(enviarBtn);
    form.addEventListener('submit', function(e) { e.preventDefault(); enviar(); });
    conversaEl.appendChild(mensagensEl); conversaEl.appendChild(form);

    painel.appendChild(topo); painel.appendChild(avisoEl); painel.appendChild(lista); painel.appendChild(conversaEl);
    fundoEl = criar('div', 'chat-fundo'); fundoEl.hidden = true;
    fundoEl.addEventListener('click', fecharPainel);
    document.body.appendChild(fundoEl); document.body.appendChild(painel);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && !painel.hidden) fecharPainel();
    });
  }

  function avisar(texto) { avisoEl.textContent = texto || ''; avisoEl.hidden = !texto; }

  function abrirPainel() {
    if (!painel) montarPainel();
    painel.hidden = false; fundoEl.hidden = false;
    document.body.classList.add('chat-aberto');
    mostrarContatos();
  }

  function fecharPainel() {
    if (!painel) return;
    painel.hidden = true; fundoEl.hidden = true;
    document.body.classList.remove('chat-aberto');
    clearInterval(timerConversa); clearInterval(timerContatos);
    atual = null;
    var botao = document.querySelector('.chat-abrir'); if (botao) botao.focus();
  }

  /* ── Contatos ──────────────────────────────────────────────── */
  function mostrarContatos() {
    clearInterval(timerConversa); atual = null;
    painel.classList.remove('em-conversa');
    tituloEl.textContent = 'Mensagens'; ligarEl.hidden = true;
    conversaEl.hidden = true; lista.hidden = false; avisar('');
    carregarContatos();
    clearInterval(timerContatos);
    timerContatos = setInterval(carregarContatos, INTERVALO_CONTATOS);
    buscaEl.focus();
  }

  function carregarContatos() {
    return api.get('/mensagens/contatos').then(function(c) {
      contatos = c; desenharContatos(); atualizarContador();
    }).catch(function(erro) { avisar(erro.message); });
  }

  function desenharContatos() {
    var ul = lista.querySelector('.chat-contatos');
    var termo = (buscaEl.value || '').toLowerCase().trim();
    ul.textContent = '';
    var visiveis = contatos.filter(function(c) {
      return !termo || c.nome.toLowerCase().indexOf(termo) !== -1 || String(c.unidade || '').indexOf(termo) !== -1;
    });
    if (!visiveis.length) {
      ul.appendChild(criar('li', 'chat-vazio', termo ? 'Ninguém com esse nome.' : 'Nenhum contato disponível.'));
      return;
    }
    visiveis.forEach(function(c) {
      var li = criar('li');
      var b = criar('button', 'chat-contato'); b.type = 'button';
      var av = criar('span', 'chat-avatar ' + c.papel);
      if (c.foto_url) { var f = criar('img'); f.src = api.arquivo(c.foto_url); f.alt = ''; av.appendChild(f); }
      else av.textContent = c.nome.split(' ').map(function(p) { return p[0]; }).slice(0, 2).join('').toUpperCase();
      var info = criar('span', 'chat-contato-info');
      info.appendChild(criar('strong', null, c.nome));
      info.appendChild(criar('span', 'chat-contato-papel',
        (ROTULO[c.papel] || c.papel) + (c.unidade ? ' · Apto ' + c.unidade : '')));
      if (c.ultima_mensagem) info.appendChild(criar('span', 'chat-contato-ultima', c.ultima_mensagem));
      b.appendChild(av); b.appendChild(info);
      if (c.nao_lidas) {
        var n = criar('span', 'chat-contato-novas', String(c.nao_lidas));
        n.setAttribute('aria-label', c.nao_lidas + ' não lida' + (c.nao_lidas > 1 ? 's' : ''));
        b.appendChild(n);
      }
      b.addEventListener('click', function() { abrirConversa(c); });
      li.appendChild(b);
      ul.appendChild(li);
    });
  }

  /* ── Conversa ──────────────────────────────────────────────── */
  function abrirConversa(c) {
    clearInterval(timerContatos);
    atual = c; ultimoId = 0;
    painel.classList.add('em-conversa');
    tituloEl.textContent = c.nome;
    if (c.telefone) { ligarEl.href = telefoneLink(c.telefone); ligarEl.hidden = false; ligarEl.title = 'Ligar para ' + c.nome; }
    lista.hidden = true; conversaEl.hidden = false; avisar('');
    mensagensEl.textContent = '';
    buscarNovas();
    clearInterval(timerConversa);
    timerConversa = setInterval(buscarNovas, INTERVALO_CONVERSA);
    campoTexto.focus();
  }

  function buscarNovas() {
    if (!atual) return;
    var alvo = atual.id;
    api.get('/mensagens/com/' + alvo + (ultimoId ? '?depois_de=' + ultimoId : ''))
      .then(function(msgs) {
        if (!atual || atual.id !== alvo) return;
        if (!ultimoId && !msgs.length) {
          mensagensEl.appendChild(criar('li', 'chat-vazio', 'Nenhuma mensagem ainda. Escreva a primeira.'));
        }
        msgs.forEach(adicionar);
        atualizarContador();
      })
      .catch(function(erro) { avisar(erro.message); });
  }

  function adicionar(m) {
    if (m.id <= ultimoId) return;
    var vazio = mensagensEl.querySelector('.chat-vazio'); if (vazio) vazio.remove();
    ultimoId = m.id;
    var li = criar('li', 'chat-msg' + (m.minha ? ' minha' : ''));
    li.appendChild(criar('p', 'chat-msg-texto', m.texto));
    li.appendChild(criar('time', 'chat-msg-hora', hora(m.enviada_em)));
    mensagensEl.appendChild(li);
    mensagensEl.scrollTop = mensagensEl.scrollHeight;
  }

  function enviar() {
    var texto = campoTexto.value.trim();
    if (!texto || !atual) return;
    campoTexto.disabled = true;
    api.post('/mensagens/com/' + atual.id, { texto: texto })
      .then(function(m) { campoTexto.value = ''; adicionar(m); avisar(''); })
      .catch(function(erro) { avisar(erro.message); })
      .then(function() { campoTexto.disabled = false; campoTexto.focus(); });
  }

  /* Abre direto a conversa com alguém (usado pela tela de porteiros). */
  function abrir(id) {
    abrirPainel();
    carregarContatos().then(function() {
      var c = contatos.filter(function(x) { return x.id === id; })[0];
      if (c) abrirConversa(c); else avisar('Este contato não está disponível para conversa.');
    });
  }

  function iniciar() { montarBotao(); }
  if (global.SmartCondo.usuario) iniciar();
  else document.addEventListener('smartcondo:sessao', iniciar, { once: true });

  global.SmartCondo.chat = { abrir: abrir, telefoneLink: telefoneLink };
})(window);
