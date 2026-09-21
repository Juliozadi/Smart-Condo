function mostrarErro(input, mensagem) {
  limparErro(input);
  const erro = document.createElement('span');
  erro.className = 'erro-validacao';
  erro.textContent = mensagem;
  input.style.borderColor = '#e74c3c';
  input.parentNode.appendChild(erro);
}

function limparErro(input) {
  input.style.borderColor = '';
  const existente = input.parentNode.querySelector('.erro-validacao');
  if (existente) existente.remove();
}

function limparTodosErros(form) {
  form.querySelectorAll('.erro-validacao').forEach(function(e) { e.remove(); });
  form.querySelectorAll('input, select, textarea').forEach(function(i) { i.style.borderColor = ''; });
}

function validarEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validarTelefone(tel) {
  return tel.replace(/\D/g, '').length >= 10;
}

function validarCPF(cpf) {
  var limpo = cpf.replace(/\D/g, '');
  if (limpo.length !== 11 || /^(\d)\1{10}$/.test(limpo)) return false;
  var soma = 0, resto, i;
  for (i = 1; i <= 9; i++) soma += parseInt(limpo[i-1]) * (11 - i);
  resto = (soma * 10) % 11;
  if (resto === 10) resto = 0;
  if (resto !== parseInt(limpo[9])) return false;
  soma = 0;
  for (i = 1; i <= 10; i++) soma += parseInt(limpo[i-1]) * (12 - i);
  resto = (soma * 10) % 11;
  if (resto === 10) resto = 0;
  return resto === parseInt(limpo[10]);
}

function validarCNPJ(cnpj) {
  var limpo = cnpj.replace(/\D/g, '');
  if (limpo.length !== 14) return false;
  var soma = 0, peso = 5, i, dig;
  for (i = 0; i < 12; i++) { soma += parseInt(limpo[i]) * peso--; if (peso < 2) peso = 9; }
  dig = soma % 11 < 2 ? 0 : 11 - soma % 11;
  if (dig !== parseInt(limpo[12])) return false;
  soma = 0; peso = 6;
  for (i = 0; i < 13; i++) { soma += parseInt(limpo[i]) * peso--; if (peso < 2) peso = 9; }
  dig = soma % 11 < 2 ? 0 : 11 - soma % 11;
  return dig === parseInt(limpo[13]);
}

function validarSenha(senha) {
  return senha.length >= 6;
}

function validarCEP(cep) {
  return /^\d{5}-?\d{3}$/.test(cep);
}

function validarPlaca(placa) {
  return /^[A-Z]{3}[0-9][0-9A-Z][0-9]{2}$/.test(placa.toUpperCase());
}

function validarVazio(valor) {
  return valor.trim() !== '';
}

function mascaraCPF(input) {
  input.addEventListener('input', function() {
    var v = this.value.replace(/\D/g, '').slice(0, 11);
    v = v.replace(/(\d{3})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    this.value = v;
  });
}

function mascaraTelefone(input) {
  input.addEventListener('input', function() {
    var v = this.value.replace(/\D/g, '').slice(0, 11);
    v = v.replace(/^(\d{2})(\d)/, '($1) $2');
    if (v.length > 10) v = v.replace(/(\d{5})(\d)/, '$1-$2');
    else v = v.replace(/(\d{4})(\d)/, '$1-$2');
    this.value = v;
  });
}

function mascaraCEP(input) {
  input.addEventListener('input', function() {
    var v = this.value.replace(/\D/g, '').slice(0, 8);
    v = v.replace(/(\d{5})(\d)/, '$1-$2');
    this.value = v;
  });
}

function mascaraCNPJ(input) {
  input.addEventListener('input', function() {
    var v = this.value.replace(/\D/g, '').slice(0, 14);
    v = v.replace(/(\d{2})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d)/, '$1.$2');
    v = v.replace(/(\d{3})(\d{1,4})$/, '$1/$2');
    this.value = v;
  });
}

function mascaraPlaca(input) {
  input.addEventListener('input', function() {
    var v = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 7);
    if (v.length > 3) v = v.slice(0, 3) + '-' + v.slice(3);
    this.value = v;
  });
}

function toggleSenha(inputId, iconeId) {
  var input = document.getElementById(inputId);
  var icone = document.getElementById(iconeId);
  if (!input || !icone) return;
  if (input.type === 'password') {
    input.type = 'text';
    icone.className = icone.className.replace('fa-eye', 'fa-eye-slash');
  } else {
    input.type = 'password';
    icone.className = icone.className.replace('fa-eye-slash', 'fa-eye');
  }
}

function criarToggleSenha(input, iconeClass) {
  var wrapper = input.parentNode;
  wrapper.style.position = 'relative';
  var icone = document.createElement('i');
  icone.className = iconeClass + ' fa-eye';
  icone.style.cssText = 'position:absolute;right:12px;top:50%;transform:translateY(-50%);cursor:pointer;color:#999;z-index:2;';
  var inputId = input.id || 'senha-' + Math.random().toString(36).slice(2, 8);
  input.id = inputId;
  icone.id = 'icone-' + inputId;
  icone.setAttribute('data-input', inputId);
  icone.setAttribute('data-icone', icone.id);
  icone.addEventListener('click', function() {
    toggleSenha(inputId, icone.id);
  });
  wrapper.appendChild(icone);
}

function initMascaras() {
  document.querySelectorAll('.mask-cpf').forEach(mascaraCPF);
  document.querySelectorAll('.mask-tel').forEach(mascaraTelefone);
  document.querySelectorAll('.mask-cep').forEach(mascaraCEP);
  document.querySelectorAll('.mask-cnpj').forEach(mascaraCNPJ);
  document.querySelectorAll('.mask-placa').forEach(mascaraPlaca);
  document.querySelectorAll('input[type="password"]').forEach(function(el) {
    if (!el.closest('.senha-wrapper-custom')) {
      criarToggleSenha(el, 'fa-regular');
    }
  });
}

var modalCriado = false;

function criarModalConfirmacao() {
  if (modalCriado) return;
  modalCriado = true;

  var estilo = document.createElement('style');
  estilo.textContent = '.md-overlay{position:fixed;inset:0;background:rgba(6,15,24,.55);backdrop-filter:blur(4px);z-index:9999;display:none;align-items:center;justify-content:center;animation:mdFadeIn .2s ease}.md-overlay.ativo{display:flex}.md-card{background:#fff;border-radius:18px;padding:32px 28px 24px;max-width:380px;width:90%;box-shadow:0 12px 40px rgba(6,15,24,.25);text-align:center;animation:mdSlideUp .25s ease;font-family:"Plus Jakarta Sans",sans-serif}.md-icon{width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#fee2e2,#fff5f5);display:flex;align-items:center;justify-content:center;margin:0 auto 16px}.md-icon i{font-size:24px;color:#e74c3c}.md-card h3{font-size:18px;font-weight:800;color:#060f18;margin:0 0 6px}.md-card p{font-size:14px;color:#6b7a84;margin:0 0 24px;line-height:1.5}.md-actions{display:flex;gap:12px}.md-actions a{flex:1;padding:12px 0;border-radius:12px;font-size:14px;font-weight:700;text-decoration:none;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;justify-content:center;gap:6px}.md-btn-cancel{background:var(--surface);color:var(--text);border:1.5px solid var(--border)}.md-btn-cancel:hover{background:var(--border)}.md-btn-confirm{background:linear-gradient(135deg,#f56c6c,#e74c3c);color:#fff;box-shadow:0 2px 6px rgba(245,108,108,.25),0 6px 16px rgba(245,108,108,.18)}.md-btn-confirm:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(245,108,108,.3),0 8px 20px rgba(245,108,108,.2)}@keyframes mdFadeIn{from{opacity:0}to{opacity:1}}@keyframes mdSlideUp{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}';
  document.head.appendChild(estilo);

  var overlay = document.createElement('div');
  overlay.className = 'md-overlay';
  overlay.id = 'md-logout';

  var card = document.createElement('div');
  card.className = 'md-card';
  card.innerHTML =
    '<div class="md-icon"><i class="fa-solid fa-right-from-bracket"></i></div>' +
    '<h3>Sair do Sistema</h3>' +
    '<p>Tem certeza que deseja sair?<br>Você será redirecionado para o login.</p>' +
    '<div class="md-actions">' +
      '<a href="javascript:void(0)" class="md-btn-cancel" onclick="fecharModal(\'md-logout\')"><i class="fa-solid fa-xmark"></i> Cancelar</a>' +
      '<a href="javascript:void(0)" class="md-btn-confirm" id="md-confirm-sair"><i class="fa-solid fa-check"></i> Sair</a>' +
    '</div>';

  overlay.appendChild(card);
  document.body.appendChild(overlay);

  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) fecharModal('md-logout');
  });
}

function abrirModal(id) {
  criarModalConfirmacao();
  document.getElementById(id).classList.add('ativo');
}

function fecharModal(id) {
  document.getElementById(id).classList.remove('ativo');
}

document.addEventListener('DOMContentLoaded', function() {
  initMascaras();
  criarModalConfirmacao();
  document.querySelectorAll('.logout-btn').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var href = this.getAttribute('href');
      if (!href || href === '#') return;
      abrirModal('md-logout');
      document.getElementById('md-confirm-sair').onclick = function() {
        window.location.href = href;
      };
    });
  });
});
