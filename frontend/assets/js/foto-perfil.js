/* ═══════════════════════════════════════════════════════════════
   SmartCondo — foto de perfil
   Botão de câmera sobre o avatar para enviar ou trocar a foto, e
   "Remover foto" quando ela existe. Usado pelas telas de perfil do
   síndico, do porteiro e do morador, que chamam fotoPerfil.mostrar()
   depois de carregar os dados.

   A verificação de tipo e tamanho aqui é só para responder rápido: quem
   decide é o servidor, que confere o conteúdo do arquivo.
   ═══════════════════════════════════════════════════════════════ */
(function(global) {
  'use strict';

  var LIMITE_MB = 2;
  var TIPOS = ['image/jpeg', 'image/png', 'image/webp'];

  var api = global.SmartCondo.api;

  function el(id) { return document.getElementById(id); }

  function avisar(texto, erro) {
    var aviso = el('fotoAviso');
    if (!aviso) return;
    aviso.textContent = texto || '';
    aviso.classList.toggle('erro', !!erro);
  }

  function mostrar(caminho) {
    var foto = el('avatarPreview'), icone = el('avatarIcon'), remover = el('fotoRemover');
    if (!foto) return;
    if (caminho) {
      foto.src = api.arquivo(caminho);
      foto.style.display = 'block';
      if (icone) icone.style.display = 'none';
      if (remover) remover.hidden = false;
    } else {
      foto.removeAttribute('src');
      foto.style.display = 'none';
      if (icone) icone.style.display = '';
      if (remover) remover.hidden = true;
    }
  }

  function enviar(arquivo) {
    if (TIPOS.indexOf(arquivo.type) === -1) {
      avisar('Escolha uma imagem JPG, PNG ou WebP.', true);
      return;
    }
    if (arquivo.size > LIMITE_MB * 1024 * 1024) {
      avisar('A foto passa de ' + LIMITE_MB + ' MB. Escolha uma imagem menor.', true);
      return;
    }
    var dados = new FormData();
    dados.append('arquivo', arquivo);
    avisar('Enviando…');
    api.put('/usuarios/eu/foto', dados)
      .then(function(perfil) { mostrar(perfil.foto_url); avisar('Foto atualizada.'); })
      .catch(function(erro) { avisar(erro.message, true); });
  }

  function montar() {
    var entrada = el('fotoArquivo'), remover = el('fotoRemover');
    // O botão da câmera é um <label>: abre o arquivo com o mouse, mas não
    // recebe foco. Vira botão de verdade para quem navega pelo teclado.
    var botao = document.querySelector('.p-foto-btn');
    if (botao && entrada) {
      botao.setAttribute('role', 'button');
      botao.tabIndex = 0;
      botao.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); entrada.click(); }
      });
    }
    if (entrada) {
      entrada.addEventListener('change', function() {
        if (this.files && this.files[0]) enviar(this.files[0]);
        this.value = '';   // permite escolher o mesmo arquivo de novo
      });
    }
    if (remover) {
      remover.addEventListener('click', function() {
        avisar('Removendo…');
        api.remover('/usuarios/eu/foto')
          .then(function() { mostrar(null); avisar('Foto removida.'); })
          .catch(function(erro) { avisar(erro.message, true); });
      });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', montar);
  else montar();

  global.fotoPerfil = { mostrar: mostrar };
})(window);
