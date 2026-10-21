/* Prestação de contas: o balancete do mês e a lista de despesas.

   Usado pelas telas do síndico (que também lança, corrige e cancela) e do
   morador (que só vê). Os números vêm prontos da API — GET
   /financeiro/balancete e /financeiro/despesas; aqui só se desenha. */
(function(global) {
  'use strict';
  var api = global.SmartCondo.api;

  var CATEGORIAS = {
    agua: 'Água', energia: 'Energia', limpeza: 'Limpeza', manutencao: 'Manutenção',
    seguranca: 'Segurança', pessoal: 'Pessoal', administracao: 'Administração',
    obras: 'Obras', outros: 'Outros'
  };
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
               'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];

  function dinheiro(valor) {
    return 'R$ ' + Number(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
  }
  function doisDigitos(n) { return ('0' + n).slice(-2); }
  function mesAtual() {
    var d = new Date();
    return d.getFullYear() + '-' + doisDigitos(d.getMonth() + 1);
  }
  function hojeIso() {
    var d = new Date();
    return d.getFullYear() + '-' + doisDigitos(d.getMonth() + 1) + '-' + doisDigitos(d.getDate());
  }
  function rotuloMes(mes) {
    var p = mes.split('-');
    return MESES[+p[1] - 1] + ' de ' + p[0];
  }
  function dataCurta(iso) {
    var p = (iso || '').split('-');
    return p.length === 3 ? p[2] + '/' + p[1] : '';
  }
  function campo(id) { return document.getElementById(id); }

  /* Preenche os elementos padrão das duas telas (ids começando com "c"). */
  function desenharBalancete(b) {
    var acumulado = Number(b.saldo_acumulado);
    campo('cSaldoAcumulado').textContent = dinheiro(acumulado);
    campo('cSaldoAcumulado').classList.toggle('negativo', acumulado < 0);
    campo('cRotuloMes').textContent = 'Saldo do caixa no fim de ' + rotuloMes(b.mes);
    campo('cReceitas').textContent = dinheiro(b.receitas);
    campo('cDespesas').textContent = dinheiro(b.despesas);
    campo('cSaldoMes').textContent = dinheiro(b.saldo_do_mes);
    campo('cSaldoAnterior').textContent = dinheiro(b.saldo_anterior);

    var lista = campo('listaCategorias');
    lista.innerHTML = '';
    var maior = b.por_categoria.reduce(function(m, c) { return Math.max(m, Number(c.total)); }, 0);
    b.por_categoria.forEach(function(c) {
      var linha = document.createElement('div');
      linha.className = 'categoria-despesa';
      var nome = document.createElement('span');
      nome.className = 'categoria-nome';
      nome.textContent = CATEGORIAS[c.categoria] || c.categoria;
      var barra = document.createElement('span');
      barra.className = 'categoria-barra';
      barra.setAttribute('aria-hidden', 'true');
      var preenchida = document.createElement('span');
      preenchida.style.width = (maior ? Math.max(2, Number(c.total) / maior * 100) : 0) + '%';
      barra.appendChild(preenchida);
      var valor = document.createElement('span');
      valor.className = 'categoria-valor';
      valor.textContent = dinheiro(c.total);
      linha.appendChild(nome);
      linha.appendChild(barra);
      linha.appendChild(valor);
      lista.appendChild(linha);
    });
    campo('estadoCategorias').textContent =
      b.por_categoria.length ? '' : 'Nenhuma despesa lançada neste mês.';
  }

  /* Um cartão por despesa. "acoes" (só o síndico) recebe a despesa e o
     cartão, e acrescenta os botões. */
  function cartaoDespesa(d, acoes) {
    var item = document.createElement('div');
    item.className = 'list-item' + (d.cancelada ? ' despesa-cancelada' : '');

    var icone = document.createElement('div');
    icone.className = 'card-icon icon-yellow';
    var img = document.createElement('img');
    img.src = '../../assets/img/icons/file-invoice-dollar.svg';
    img.width = 16; img.height = 16; img.alt = '';
    icone.appendChild(img);

    var info = document.createElement('div');
    info.className = 'list-info';
    var titulo = document.createElement('h3');
    titulo.textContent = d.descricao;
    var sub = document.createElement('p');
    var partes = [CATEGORIAS[d.categoria] || d.categoria, dataCurta(d.data)];
    if (d.fornecedor) partes.push(d.fornecedor);
    if (d.cancelada) partes.push('cancelada');
    sub.textContent = partes.join(' · ');
    info.appendChild(titulo);
    info.appendChild(sub);
    if (d.ultima_alteracao && global.SmartCondo.ui) {
      var autoria = document.createElement('small');
      autoria.className = 'lista-autoria';
      autoria.textContent = global.SmartCondo.ui.textoAlteracao(d.ultima_alteracao);
      info.appendChild(autoria);
    }

    item.appendChild(icone);
    item.appendChild(info);

    if (d.comprovante_url) {
      var ver = document.createElement('button');
      ver.type = 'button';
      ver.className = 'contato-btn';
      ver.textContent = 'Comprovante';
      ver.setAttribute('aria-label', 'Abrir o comprovante de ' + d.descricao);
      ver.addEventListener('click', function() {
        api.abrirArquivo(d.comprovante_url, 'Comprovante — ' + d.descricao)
          .catch(function(e) { alert(e.message); });
      });
      item.appendChild(ver);
    }
    if (acoes) acoes(d, item);

    var valor = document.createElement('span');
    valor.className = 'valor-despesa';
    valor.textContent = dinheiro(d.valor);
    item.appendChild(valor);
    return item;
  }

  function carregar(mes) {
    return Promise.all([
      api.get('/financeiro/balancete?mes=' + mes),
      api.get('/financeiro/despesas?mes=' + mes)
    ]);
  }

  global.SmartCondo.contas = {
    CATEGORIAS: CATEGORIAS, dinheiro: dinheiro, mesAtual: mesAtual, hojeIso: hojeIso,
    rotuloMes: rotuloMes, desenharBalancete: desenharBalancete,
    cartaoDespesa: cartaoDespesa, carregar: carregar
  };
})(window);
