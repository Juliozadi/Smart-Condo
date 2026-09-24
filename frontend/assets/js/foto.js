/* ═══════════════════════════════════════════════════════════════
   SmartCondo — Captura de foto (vídeo porteiro)
   Documentação, seções 6 e 8:
     "uma notificação seja enviada para o cliente com a foto do indivíduo
      ou gravação em tempo real (vídeo porteiro), para que ele seja
      identificado e, assim, o cliente confirme se é ou não seu convidado"
     "o porteiro me envia pelo sistema uma foto ou vídeo para que eu
      confirmasse a minha entrega ou pedido"

   Faz o upgrade de qualquer elemento .captura-foto do HTML. Usa a câmera
   do dispositivo quando disponível e cai para upload de arquivo quando não
   há permissão, câmera ou contexto seguro (https/localhost).
   ═══════════════════════════════════════════════════════════════ */
(function() {
  'use strict';

  function temCamera() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  // A foto vai para a API como JPEG de até 1280 px no lado maior: a do
  // celular costuma passar do limite de 2 MB, e para reconhecer alguém na
  // portaria não precisa de mais que isso.
  var LADO_MAXIMO = 1280;
  function comoJpeg(origem, largura, altura) {
    var escala = Math.min(1, LADO_MAXIMO / Math.max(largura, altura));
    var canvas = document.createElement('canvas');
    canvas.width = Math.round(largura * escala);
    canvas.height = Math.round(altura * escala);
    canvas.getContext('2d').drawImage(origem, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.85);
  }

  function montar(campo) {
    if (campo.dataset.montado) return;
    campo.dataset.montado = '1';

    var rotulo  = campo.getAttribute('data-rotulo') || 'Foto';
    var dica    = campo.getAttribute('data-dica') || '';
    var nomeArq = campo.getAttribute('data-input') || 'foto';
    var pronta  = campo.getAttribute('data-pronta') ||
                  'Imagem pronta. Ela será enviada ao morador junto com a notificação.';

    campo.innerHTML =
      '<label class="captura-rotulo">' +
        '<img src="' + campo.getAttribute('data-icone') + '" width="16" height="16" alt="">' + rotulo +
      '</label>' +
      (dica ? '<p class="captura-dica">' + dica + '</p>' : '') +
      '<div class="captura-palco">' +
        '<video class="captura-video" playsinline muted hidden></video>' +
        '<div class="captura-vazio">' +
          '<img src="' + campo.getAttribute('data-icone') + '" width="26" height="26" alt="" aria-hidden="true">' +
          '<span>Nenhuma imagem ainda</span>' +
        '</div>' +
      '</div>' +
      '<div class="captura-acoes">' +
        '<button type="button" class="captura-btn abrir">Abrir câmera</button>' +
        '<button type="button" class="captura-btn tirar" hidden>Capturar</button>' +
        '<button type="button" class="captura-btn refazer" hidden>Refazer</button>' +
        '<label class="captura-btn secundario">Enviar arquivo' +
          '<input type="file" accept="image/*" capture="environment" hidden>' +
        '</label>' +
      '</div>' +
      '<p class="captura-status" role="status"></p>' +
      '<input type="hidden" name="' + nomeArq + '" class="captura-valor">';

    var video   = campo.querySelector('.captura-video');
    var imagem  = null;
    var vazio   = campo.querySelector('.captura-vazio');
    var status  = campo.querySelector('.captura-status');
    var valor   = campo.querySelector('.captura-valor');
    var bAbrir  = campo.querySelector('.captura-btn.abrir');
    var bTirar  = campo.querySelector('.captura-btn.tirar');
    var bRefaz  = campo.querySelector('.captura-btn.refazer');
    var arquivo = campo.querySelector('input[type="file"]');

    var stream = null;

    function avisar(texto, erro) {
      status.textContent = texto || '';
      status.classList.toggle('erro', !!erro);
    }

    function pararCamera() {
      if (stream) {
        stream.getTracks().forEach(function(t) { t.stop(); });
        stream = null;
      }
      video.hidden = true;
    }

    function mostrarFoto(dataUrl) {
      pararCamera();
      if (!imagem) {
        imagem = document.createElement('img');
        imagem.className = 'captura-imagem';
        imagem.alt = 'Pré-visualização da foto capturada';
        campo.querySelector('.captura-palco').appendChild(imagem);
      }
      imagem.src = dataUrl;
      imagem.hidden = false;
      vazio.hidden = true;
      valor.value = dataUrl;
      bAbrir.hidden = true;
      bTirar.hidden = true;
      bRefaz.hidden = false;
      campo.classList.add('tem-foto');
      avisar(pronta);
      campo.dispatchEvent(new CustomEvent('foto:capturada', { bubbles: true }));
    }

    if (!temCamera()) {
      bAbrir.hidden = true;
      avisar('Câmera indisponível neste dispositivo — envie um arquivo de imagem.');
    }

    bAbrir.addEventListener('click', function() {
      avisar('Solicitando acesso à câmera…');
      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
        .then(function(s) {
          stream = s;
          video.srcObject = s;
          video.hidden = false;
          vazio.hidden = true;
          if (imagem) imagem.hidden = true;
          video.play();
          bAbrir.hidden = true;
          bTirar.hidden = false;
          avisar('Câmera ativa — enquadre e capture.');
        })
        .catch(function() {
          avisar('Não foi possível acessar a câmera. Envie um arquivo de imagem.', true);
        });
    });

    bTirar.addEventListener('click', function() {
      if (!stream) return;
      mostrarFoto(comoJpeg(video, video.videoWidth || 640, video.videoHeight || 480));
    });

    function limpar() {
      pararCamera();
      if (imagem) { imagem.remove(); imagem = null; }
      vazio.hidden = false;
      valor.value = '';
      arquivo.value = '';
      bRefaz.hidden = true;
      bTirar.hidden = true;
      bAbrir.hidden = !temCamera();
      campo.classList.remove('tem-foto');
      avisar('');
    }
    bRefaz.addEventListener('click', limpar);
    // O reset do formulário não mexe em campo oculto nem na prévia.
    var formulario = campo.closest('form');
    if (formulario) formulario.addEventListener('reset', limpar);

    arquivo.addEventListener('change', function() {
      var f = this.files && this.files[0];
      if (!f) return;
      if (!/^image\//.test(f.type)) {
        avisar('Selecione um arquivo de imagem.', true);
        return;
      }
      // Passa pelo canvas: reduz o tamanho e converte qualquer formato
      // que o navegador abra (HEIC do iPhone, GIF…) para JPEG.
      var endereco = URL.createObjectURL(f);
      var img = new Image();
      img.onload = function() {
        URL.revokeObjectURL(endereco);
        mostrarFoto(comoJpeg(img, img.naturalWidth, img.naturalHeight));
      };
      img.onerror = function() {
        URL.revokeObjectURL(endereco);
        avisar('Não foi possível abrir esta imagem. Tente uma foto JPG ou PNG.', true);
      };
      img.src = endereco;
    });

    // Libera a câmera ao sair da página
    window.addEventListener('pagehide', pararCamera);
  }

  function iniciar() {
    document.querySelectorAll('.captura-foto').forEach(montar);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
