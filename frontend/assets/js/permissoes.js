/* Permissões do porteiro no front-end.
 *
 * O síndico decide, por porteiro, o que ele pode registrar (documentação,
 * seção 9, "Permissão do Porteiro"). A API já recusa o que não foi
 * liberado, com 403. Sem isto aqui, porém, o porteiro via o módulo no
 * menu, abria a tela, preenchia o formulário inteiro e só descobria no
 * envio que não podia — o que parece defeito do sistema.
 *
 * Isto é conveniência, não segurança: quem decide continua sendo a API.
 */
(function(global) {
  'use strict';

  var api = global.SmartCondo && global.SmartCondo.api;

  // Qual permissão cada tela exige.
  var EXIGE = {
    'visitantes.html': 'registrar_visitantes',
    'encomendas.html': 'registrar_encomendas',
    'veiculos.html': 'registrar_veiculos',
    'ocorrencias.html': 'registrar_ocorrencias',
  };

  function buscar(usuario) {
    if (!usuario || usuario.papel !== 'porteiro') return Promise.resolve(null);
    return api.get('/usuarios/eu/permissoes')
      .catch(function() { return null; });   // sem resposta, não bloqueia nada
  }

  /* Some com os cartões e itens de menu que levam ao que o porteiro não
     pode fazer. */
  function aplicarNoMenu(permissoes) {
    if (!permissoes) return;
    Object.keys(EXIGE).forEach(function(pagina) {
      if (permissoes[EXIGE[pagina]]) return;
      var seletor = 'a[href="' + pagina + '"], a[href$="/' + pagina + '"]';
      Array.prototype.forEach.call(document.querySelectorAll(seletor), function(link) {
        var cartao = link.closest('.dash-card') || link;
        cartao.hidden = true;
      });
    });
  }

  /* Guarda de tela: se o porteiro abrir a página pelo endereço direto,
     explica e devolve ao painel em vez de deixar tentar. */
  function guardarTela(permissoes, arquivo) {
    if (!permissoes) return true;
    var exigida = EXIGE[arquivo];
    if (!exigida || permissoes[exigida]) return true;
    var aviso = document.createElement('div');
    aviso.className = 'alert-box warning';
    aviso.setAttribute('role', 'alert');
    aviso.textContent = 'O síndico não liberou esta função para o seu usuário. '
      + 'Fale com ele se precisar de acesso.';
    var onde = document.querySelector('main') || document.body;
    onde.insertBefore(aviso, onde.firstChild);
    Array.prototype.forEach.call(document.querySelectorAll('form'), function(f) {
      f.hidden = true;
    });
    return false;
  }

  global.SmartCondo = global.SmartCondo || {};
  global.SmartCondo.permissoes = {
    buscar: buscar,
    aplicarNoMenu: aplicarNoMenu,
    guardarTela: guardarTela,

    /* Chamada única das telas do porteiro. Devolve a promessa das
       permissões para quem quiser usá-las também. */
    aplicar: function(usuario) {
      var arquivo = (global.location.pathname.split('/').pop() || '');
      return buscar(usuario).then(function(p) {
        aplicarNoMenu(p);
        guardarTela(p, arquivo);
        return p;
      });
    }
  };
})(window);
