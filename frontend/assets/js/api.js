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

    // opcoes.token troca o token da sessão por outro — o do envio dos
    // documentos do cadastro, que não abre sessão.
    var token = opcoes.token || sessao.token();
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
        if (resposta.status === 401 && token && !opcoes.token && opcoes.semRedirecionar !== true) {
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

    /* Arquivo que só sai com o token (foto de visitante, documento do
       cadastro). Uma <img src> não manda o cabeçalho Authorization, então
       o arquivo é baixado aqui e vira um endereço blob: local. Quem usa
       deve chamar URL.revokeObjectURL quando a imagem sair da tela. */
    protegido: function(caminho) {
      var token = sessao.token();
      return fetch(API + caminho, {
        headers: token ? { 'Authorization': 'Bearer ' + token } : {}
      }).then(function(resposta) {
        if (!resposta.ok) {
          throw new ErroApi(resposta.status === 404
            ? 'Arquivo não encontrado.'
            : 'Não foi possível abrir o arquivo (erro ' + resposta.status + ').', resposta.status);
        }
        return resposta.blob();
      }, function() {
        throw new ErroApi('Não foi possível falar com o servidor. Verifique se a API está no ar.', 0);
      }).then(function(blob) {
        return { url: URL.createObjectURL(blob), tipo: blob.type };
      });
    },

    /* Mostra numa <img> um arquivo protegido; se não der, chama "falhou". */
    imagemProtegida: function(img, caminho, falhou) {
      return api.protegido(caminho).then(function(arquivo) {
        function soltar() { URL.revokeObjectURL(arquivo.url); }
        img.addEventListener('load', soltar, { once: true });
        img.addEventListener('error', soltar, { once: true });
        img.src = arquivo.url;
      }).catch(function() { if (falhou) falhou(); });
    },

    /* Abre um arquivo protegido (documento do condomínio) numa nova aba.
       A aba é aberta já no clique — depois do download o navegador a
       trataria como pop-up e bloquearia — e recebe o arquivo quando ele
       chega. Se mesmo assim não abrir, o arquivo é baixado. */
    abrirArquivo: function(caminho, nome) {
      var janela = global.open('', '_blank');
      if (janela) {
        janela.opener = null;
        janela.document.title = 'Abrindo…';
        janela.document.body.textContent = 'Abrindo o arquivo…';
      }
      return api.protegido(caminho).then(function(arquivo) {
        if (janela && !janela.closed) {
          janela.location.href = arquivo.url;
        } else {
          var link = document.createElement('a');
          link.href = arquivo.url;
          link.download = nome || 'documento';
          document.body.appendChild(link);
          link.click();
          link.remove();
        }
        setTimeout(function() { URL.revokeObjectURL(arquivo.url); }, 60000);
      }, function(erro) {
        if (janela) janela.close();
        throw erro;
      });
    },

    /* Troca o conteúdo de "caixa" (ícone, iniciais) pela foto protegida,
       se ela abrir. Se não abrir, a caixa fica como estava. */
    trocarPorFoto: function(caixa, caminho, alt) {
      if (!caminho) return;
      var img = document.createElement('img');
      img.className = 'foto-registro';
      img.alt = alt || '';
      api.protegido(caminho).then(function(arquivo) {
        function soltar() { URL.revokeObjectURL(arquivo.url); }
        img.addEventListener('load', function() {
          soltar();
          caixa.textContent = '';
          caixa.classList.add('com-foto');
          caixa.appendChild(img);
        }, { once: true });
        img.addEventListener('error', soltar, { once: true });
        img.src = arquivo.url;
      }).catch(function() {});
    },

    /* Espera antes de deixar pedir outro código. A API só emite um código
       por minuto por pessoa (contra disparos de e-mail e SMS); sem esta
       espera, o clique parecia funcionar e nada chegava. */
    esperarReenvio: function(link, segundos) {
      var texto = 'Reenviar código';
      var resta = segundos || 60;
      link.dataset.aguardando = '1';
      link.setAttribute('aria-disabled', 'true');
      link.classList.add('link-aguardando');
      function atualizar() {
        if (resta <= 0) {
          clearInterval(relogio);
          delete link.dataset.aguardando;
          link.removeAttribute('aria-disabled');
          link.classList.remove('link-aguardando');
          link.textContent = texto;
          return;
        }
        link.textContent = 'Reenviar em ' + resta + ' s';
        resta -= 1;
      }
      var relogio = setInterval(atualizar, 1000);
      atualizar();
    },

    /* Envia a foto capturada (data URL) para a rota dada. Resolve com
       null se deu certo ou não havia foto, e com a mensagem do erro se
       falhou — o registro já existe, então a falha da foto não o desfaz. */
    anexarFoto: function(rota, dataUrl) {
      if (!dataUrl) return Promise.resolve(null);
      return api.put(rota, api.arquivoDeDataUrl(dataUrl, 'foto.jpg'))
        .then(function() { return null; }, function(e) { return e.message; });
    },

    /* Miniatura de uma foto protegida; clicar abre a imagem inteira numa
       nova aba. Enquanto carrega, ou se não carregar, fica invisível. */
    miniatura: function(caminho, alt) {
      var link = document.createElement('a');
      link.className = 'miniatura-foto';
      link.target = '_blank';
      link.rel = 'noopener';
      link.hidden = true;
      link.title = 'Abrir a foto';
      var img = document.createElement('img');
      img.alt = alt || 'Foto anexada';
      link.appendChild(img);
      api.protegido(caminho).then(function(arquivo) {
        img.addEventListener('load', function() { link.hidden = false; }, { once: true });
        img.src = arquivo.url;
        link.href = arquivo.url;
      }).catch(function() {});
      return link;
    },

    /* Um data URL (a foto capturada pela câmera) como arquivo para envio. */
    arquivoDeDataUrl: function(dataUrl, nome) {
      var partes = dataUrl.split(',');
      var tipo = (partes[0].match(/data:([^;]+)/) || [])[1] || 'application/octet-stream';
      var binario = atob(partes[1] || '');
      var bytes = new Uint8Array(binario.length);
      for (var i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
      var dados = new FormData();
      dados.append('arquivo', new Blob([bytes], { type: tipo }), nome || 'foto.jpg');
      return dados;
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
