/* ═══════════════════════════════════════════════════════════════
   SmartCondo — camada de acesso à API
   Centraliza a URL base, o token da sessão, o envio das requisições e
   o tratamento de erro. Todas as telas usam este arquivo em vez de
   chamar fetch() diretamente.
   ═══════════════════════════════════════════════════════════════ */
(function(global) {
  'use strict';

  // ── URL da API ────────────────────────────────────────────────
  // Pode ser sobrescrita antes de carregar este arquivo com:
  //   <script>window.SMARTCONDO_API = 'https://api.exemplo.com/api/v1';</script>
  var API = global.SMARTCONDO_API || (function() {
    var proto = global.location.protocol;
    var host = global.location.hostname || 'localhost';
    // Aberto via file:// não tem host; assume a API local.
    if (proto === 'file:') return 'http://localhost:8000/api/v1';
    return proto + '//' + host + ':8000/api/v1';
  })();

  // ── Caminho relativo até a raiz do projeto ────────────────────
  // As páginas ficam em profundidades diferentes (index.html na raiz,
  // pages/morador/x.html dois níveis abaixo). O caminho sai do src
  // deste próprio arquivo, que termina em "assets/js/": o que vem
  // antes é a raiz. Assim não importa de que pasta o site é servido
  // nem se a página foi aberta direto do disco.
  var BASE = (function() {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].getAttribute('src') || '';
      var corte = src.indexOf('assets/js/');
      if (corte !== -1) return src.slice(0, corte);
    }
    return '';
  })();

  var CHAVE_TOKEN = 'smartcondo_token';
  var CHAVE_USUARIO = 'smartcondo_usuario';

  // ── Sessão ────────────────────────────────────────────────────
  var sessao = {
    token: function() {
      try { return localStorage.getItem(CHAVE_TOKEN); } catch (_) { return null; }
    },
    usuario: function() {
      try { return JSON.parse(localStorage.getItem(CHAVE_USUARIO)); } catch (_) { return null; }
    },
    abrir: function(token, usuario) {
      try {
        localStorage.setItem(CHAVE_TOKEN, token);
        localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
      } catch (_) {}
    },
    encerrar: function() {
      try {
        localStorage.removeItem(CHAVE_TOKEN);
        localStorage.removeItem(CHAVE_USUARIO);
      } catch (_) {}
    },
    ativa: function() { return !!sessao.token(); }
  };

  // ── Erro da API ───────────────────────────────────────────────
  // Carrega a mensagem pronta para a tela e, quando houver, os campos
  // que o servidor recusou.
  function ErroApi(mensagem, status, campos) {
    this.name = 'ErroApi';
    this.message = mensagem;
    this.status = status;
    this.campos = campos || [];
  }
  ErroApi.prototype = Object.create(Error.prototype);
  ErroApi.prototype.constructor = ErroApi;

  function mensagemDeCampos(campos) {
    if (!campos.length) return 'Há campos inválidos.';
    // Mostra a primeira mensagem, que é a mais útil para o usuário.
    var primeiro = campos[0];
    var nome = (primeiro.loc || []).slice(-1)[0];
    var texto = (primeiro.msg || '').replace(/^Value error,\s*/, '');
    return nome ? nome + ': ' + texto : texto;
  }

  // ── Requisição ────────────────────────────────────────────────
  function requisitar(metodo, rota, corpo, opcoes) {
    opcoes = opcoes || {};

    var cabecalhos = { 'Accept': 'application/json' };
    // Arquivo (FormData) vai como está: o navegador monta o
    // Content-Type com a fronteira do multipart sozinho.
    var ehArquivo = typeof FormData !== 'undefined' && corpo instanceof FormData;
    if (corpo !== undefined && corpo !== null && !ehArquivo) {
      cabecalhos['Content-Type'] = 'application/json';
    }

    var token = sessao.token();
    if (token && opcoes.semToken !== true) {
      cabecalhos['Authorization'] = 'Bearer ' + token;
    }

    return fetch(API + rota, {
      method: metodo,
      headers: cabecalhos,
      body: ehArquivo ? corpo : (corpo !== undefined && corpo !== null ? JSON.stringify(corpo) : undefined)
    }).then(function(resposta) {
      // 204 e afins não têm corpo.
      if (resposta.status === 204) return null;

      return resposta.text().then(function(texto) {
        var dados = null;
        try { dados = texto ? JSON.parse(texto) : null; } catch (_) {}

        if (resposta.ok) return dados;

        // O token venceu ou foi revogado: derruba a sessão.
        if (resposta.status === 401 && token && opcoes.semRedirecionar !== true) {
          sessao.encerrar();
          global.location.href = BASE + 'index.html?sessao=expirada';
          // A navegação é assíncrona; interrompe a cadeia aqui.
          throw new ErroApi('Sua sessão expirou.', 401);
        }

        var campos = (dados && dados.campos) || [];
        var mensagem =
          (dados && dados.detalhe) ||
          (campos.length ? mensagemDeCampos(campos) : null) ||
          ('Não foi possível concluir (erro ' + resposta.status + ').');

        throw new ErroApi(mensagem, resposta.status, campos);
      });
    }, function(falhaDeRede) {
      if (falhaDeRede instanceof ErroApi) throw falhaDeRede;
      throw new ErroApi(
        'Não foi possível falar com o servidor. Verifique se a API está no ar.', 0
      );
    });
  }

  // ── API pública ───────────────────────────────────────────────
  var api = {
    url: API,
    base: BASE,
    sessao: sessao,
    ErroApi: ErroApi,

    get:    function(rota, opcoes)        { return requisitar('GET', rota, null, opcoes); },
    post:   function(rota, corpo, opcoes) { return requisitar('POST', rota, corpo, opcoes); },
    put:    function(rota, corpo, opcoes) { return requisitar('PUT', rota, corpo, opcoes); },
    patch:  function(rota, corpo, opcoes) { return requisitar('PATCH', rota, corpo, opcoes); },
    remover:function(rota, opcoes)        { return requisitar('DELETE', rota, null, opcoes); },

    /* Endereço completo de um arquivo servido pela API (foto de perfil).
       O servidor guarda o caminho relativo, "/arquivos/fotos/…", para
       que o registro continue válido se a API mudar de endereço. */
    arquivo: function(caminho) {
      if (!caminho) return '';
      if (/^https?:\/\//.test(caminho)) return caminho;
      return API + caminho;
    },

    /* Faz o login e guarda a sessão. Devolve o usuário autenticado. */
    entrar: function(email, senha) {
      return api.post('/auth/login', { email: email, senha: senha }, { semToken: true })
        .then(function(dados) {
          sessao.abrir(dados.access_token, dados.usuario);
          return dados.usuario;
        });
    },

    sair: function() {
      sessao.encerrar();
      global.location.href = BASE + 'index.html';
    },

    /* Para onde cada papel vai depois de entrar. */
    painelDoPapel: function(papel) {
      return BASE + 'pages/' + papel + '/dashboard.html';
    },

    /* Guarda de rota: chame no topo de cada página autenticada.
       Sem sessão, ou com papel diferente do exigido, manda para o lugar
       certo em vez de mostrar uma tela que não é do usuário. */
    protegerPagina: function(papelExigido) {
      var usuario = sessao.usuario();
      if (!sessao.ativa() || !usuario) {
        global.location.href = BASE + 'index.html?sessao=necessaria';
        return null;
      }
      if (papelExigido && usuario.papel !== papelExigido) {
        global.location.href = api.painelDoPapel(usuario.papel);
        return null;
      }
      return usuario;
    }
  };

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.api = api;
})(window);
