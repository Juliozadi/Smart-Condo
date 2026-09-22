/* Monta a documentação do trabalho em .docx, seguindo a ABNT (NBR 14724):
 * A4, margens de 3 cm (superior/esquerda) e 2 cm (inferior/direita),
 * Arial 12 com entrelinhas de 1,5, recuo de 1,25 cm na primeira linha,
 * seções primárias em nova página e paginação no canto superior direito,
 * contada a partir da folha de rosto e exibida a partir da introdução.
 *
 *   node montar.js        (o paginar.py chama este script e preenche
 *                          os números de página do sumário e das listas)
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  Header, Footer, PageNumber, TabStopType, LeaderType, VerticalAlign,
  PageOrientation, convertMillimetersToTwip,
} = require('docx');

const AQUI = __dirname;
const RAIZ = path.join(AQUI, '..');
const SAIDA = path.join(RAIZ, 'Documentacao_Concessionaria_ABNT.docx');
const resultados = JSON.parse(fs.readFileSync(path.join(AQUI, 'resultados.json'), 'utf8'));
const SCRIPT = fs.readFileSync(path.join(RAIZ, 'script_concessionaria.sql'), 'utf8');
const ARQ_PAGINAS = path.join(AQUI, 'paginas.json');
const paginas = fs.existsSync(ARQ_PAGINAS)
  ? JSON.parse(fs.readFileSync(ARQ_PAGINAS, 'utf8')) : {};

const FONTE = 'Arial';
const MONO = 'Courier New';
const CM = (n) => convertMillimetersToTwip(n * 10);
const RECUO = CM(1.25);
const LARGURA_RETRATO = CM(16);     // 21 - 3 - 2
const LARGURA_PAISAGEM = CM(24.7);  // 29,7 - 3 - 2

// ── Trechos do script ───────────────────────────────────────────────
/* Recorta o script do início de `inicio` até o fim de `fim`, sem as
 * linhas de faixa (-- ----) e títulos de etapa, que só organizam o
 * arquivo. Assim o código do documento é sempre o código do script. */
function trecho(inicio, fim, { ultimo = false } = {}) {
  const i = SCRIPT.indexOf(inicio);
  if (i < 0) throw new Error('trecho não encontrado: ' + inicio);
  const j = ultimo ? SCRIPT.lastIndexOf(fim) : SCRIPT.indexOf(fim, i);
  if (j < 0) throw new Error('fim de trecho não encontrado: ' + fim);
  return SCRIPT.slice(i, j + fim.length)
    .split('\n')
    .filter((l) => !/^-- -{5,}$/.test(l) && !/^-- \d\) /.test(l) && !/^-- {4}\S/.test(l))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// ── Texto com marcação simples ──────────────────────────────────────
/* **negrito**, *itálico*, `código` e ==destaque== (campos que o grupo
 * precisa preencher ficam com fundo amarelo). */
function runs(texto, base = {}) {
  const partes = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|==[^=]+==)/g;
  let ultimo = 0;
  let m;
  const run = (text, extra = {}) => new TextRun({
    text, font: FONTE, size: 24, ...base, ...extra,
  });
  while ((m = re.exec(texto))) {
    if (m.index > ultimo) partes.push(run(texto.slice(ultimo, m.index)));
    const t = m[0];
    if (t.startsWith('**')) partes.push(run(t.slice(2, -2), { bold: true }));
    else if (t.startsWith('==')) partes.push(run(t.slice(2, -2), { highlight: 'yellow' }));
    else if (t.startsWith('*')) partes.push(run(t.slice(1, -1), { italics: true }));
    else partes.push(run(t.slice(1, -1), { font: MONO, size: Math.round((base.size || 24) * 0.92) }));
    ultimo = m.index + t.length;
  }
  if (ultimo < texto.length) partes.push(run(texto.slice(ultimo)));
  return partes;
}

// ── Referências cruzadas: {F:id}, {Q:id}, {C:id} ────────────────────
const ROTULO = { figura: 'Figura', quadro: 'Quadro', codigo: 'Código' };
const numeros = {};
function numerar(blocos) {
  const cont = { figura: 0, quadro: 0, codigo: 0 };
  blocos.forEach((b) => {
    if (ROTULO[b.t]) {
      cont[b.t] += 1;
      b.numero = cont[b.t];
      if (b.id && numeros[b.id]) throw new Error('id repetido: ' + b.id);
      if (b.id) numeros[b.id] = `${ROTULO[b.t]} ${b.numero}`;
    }
  });
}
function resolver(texto) {
  return texto.replace(/\{[FQC]:(\w+)\}/g, (_, id) => {
    if (!numeros[id]) throw new Error('referência desconhecida: ' + id);
    return numeros[id];
  });
}

// ── Blocos de texto ─────────────────────────────────────────────────
function paragrafo(texto, opcoes = {}) {
  return new Paragraph({
    children: runs(resolver(texto)),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 0 },
    indent: { firstLine: opcoes.semRecuo ? 0 : RECUO },
  });
}

function alineas(itens) {
  const letras = 'abcdefghijklmnopqrstuvwxyz';
  return itens.map((item, i) => new Paragraph({
    children: [
      new TextRun({ text: `${letras[i]})`, font: FONTE, size: 24 }),
      new TextRun({ text: '\t', font: FONTE, size: 24 }),
      ...runs(resolver(item)),
    ],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 0 },
    indent: { left: RECUO + CM(0.7), hanging: CM(0.7) },
  }));
}

const titulos = [];   // para o sumário
const legendas = [];  // para as listas de figuras, quadros e códigos
const ordem = [];     // títulos e legendas na ordem do texto (para o paginar.py)

function titulo(nivel, numero, texto) {
  const exibido = nivel <= 2 ? texto.toUpperCase() : texto;
  titulos.push({ nivel, numero, texto: exibido });
  ordem.push(`${numero} ${exibido}`);
  return new Paragraph({
    heading: [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3][nivel - 1],
    children: [new TextRun({
      text: `${numero} ${exibido}`, font: FONTE, size: 24,
      bold: nivel !== 2, color: '000000',
    })],
    alignment: AlignmentType.LEFT,
    pageBreakBefore: nivel === 1,
    keepNext: true,
    spacing: nivel === 1 ? { before: 0, after: 360, line: 360 }
      : { before: 360, after: 360, line: 360 },
  });
}

/* Título sem indicativo numérico (resumo, listas, sumário, referências) */
function tituloCentral(texto, noSumario = false) {
  if (noSumario) {
    titulos.push({ nivel: 0, numero: '', texto });
    ordem.push(texto);
  }
  return new Paragraph({
    heading: noSumario ? HeadingLevel.HEADING_1 : undefined,
    children: [new TextRun({ text: texto, font: FONTE, size: 24, bold: true, color: '000000' })],
    alignment: AlignmentType.CENTER,
    pageBreakBefore: true,
    spacing: { before: 0, after: 360, line: 360 },
  });
}

function legendaTitulo(tipo, numero, texto) {
  const completo = `${ROTULO[tipo]} ${numero} – ${texto}`;
  legendas.push({ tipo, texto: completo });
  ordem.push(completo);
  return new Paragraph({
    children: [new TextRun({ text: completo, font: FONTE, size: 20 })],
    alignment: AlignmentType.CENTER,
    keepNext: true,
    keepLines: true,
    spacing: { before: 240, after: 80, line: 240 },
  });
}

function legendaFonte(texto) {
  return new Paragraph({
    children: runs(texto, { size: 20 }),
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 240, line: 240 },
  });
}
const FONTE_AUTORES = 'Fonte: Elaborado pelos autores (2026).';
const FONTE_EXECUCAO = `Fonte: Elaborado pelos autores, a partir da execução no MySQL ${resultados.versao.split('-')[0]} (2026).`;
const textoDaFonte = (b) => (b.fonteTexto === 'execucao' ? FONTE_EXECUCAO
  : b.fonteTexto || FONTE_AUTORES);

// ── Quadros ─────────────────────────────────────────────────────────
const borda = (cor = '000000', size = 4) => ({ style: BorderStyle.SINGLE, size, color: cor });
const BORDAS = {
  top: borda(), bottom: borda(), left: borda(), right: borda(),
  insideHorizontal: borda(), insideVertical: borda(),
};

function quadro(b, largura) {
  const fonte = b.fonte || 20;
  const total = b.larguras.reduce((x, y) => x + y, 0);
  const colunas = b.larguras.map((f) => Math.round((f / total) * largura));
  const numerico = (v) => /^-?\d+(\.\d+)?$/.test(v);
  const celula = (valor, j, cabecalho) => new TableCell({
    width: { size: colunas[j], type: WidthType.DXA },
    shading: cabecalho ? { type: ShadingType.CLEAR, fill: 'E7E9EC', color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: String(valor).split('\n').map((linhaTexto) => new Paragraph({
      children: b.mono && b.mono.includes(j) && !cabecalho
        ? [new TextRun({ text: linhaTexto, font: MONO, size: fonte - 2 })]
        : runs(linhaTexto, { size: fonte, bold: cabecalho || undefined }),
      alignment: !cabecalho && b.alinharNumeros && numerico(valor)
        ? AlignmentType.RIGHT : AlignmentType.LEFT,
      spacing: { line: 240, after: 0 },
    })),
  });
  return new Table({
    columnWidths: colunas,
    width: { size: largura, type: WidthType.DXA },
    borders: BORDAS,
    rows: [b.cabecalho, ...b.linhas].map((linha, i) => new TableRow({
      tableHeader: i === 0,
      cantSplit: true,
      children: linha.map((v, j) => celula(v, j, i === 0)),
    })),
  });
}

// ── Código SQL, com realce simples ──────────────────────────────────
const PALAVRAS = new Set(('SELECT FROM WHERE INSERT INTO VALUES UPDATE SET DELETE CREATE ' +
  'TABLE DATABASE DROP IF EXISTS USE PRIMARY KEY FOREIGN REFERENCES CONSTRAINT UNIQUE ' +
  'CHECK DEFAULT NOT NULL AUTO_INCREMENT ENGINE CHARACTER COLLATE ON CASCADE RESTRICT ' +
  'START TRANSACTION COMMIT AS JOIN LEFT ORDER BY GROUP UNION ALL COUNT SUM COALESCE ' +
  'CONCAT IN NAMES DESC AND OR INT VARCHAR DECIMAL YEAR DATE').split(' '));
const COR = { palavra: '1F3A5F', texto: '8B2E16', comentario: '6B7280' };

function linhaDeCodigo(linhaTexto, tamanho) {
  const run = (text, extra = {}) => new TextRun({ text, font: MONO, size: tamanho, ...extra });
  if (linhaTexto === '') return [run('')];
  const saida = [];
  // separa o comentário (-- fora de string)
  let codigo = linhaTexto;
  let comentario = '';
  let dentro = false;
  for (let i = 0; i < linhaTexto.length - 1; i++) {
    if (linhaTexto[i] === "'") dentro = !dentro;
    if (!dentro && linhaTexto[i] === '-' && linhaTexto[i + 1] === '-') {
      codigo = linhaTexto.slice(0, i);
      comentario = linhaTexto.slice(i);
      break;
    }
  }
  const re = /('[^']*'|[A-Za-z_]+|[^A-Za-z_']+)/g;
  let m;
  while ((m = re.exec(codigo))) {
    const t = m[0];
    if (t.startsWith("'")) saida.push(run(t, { color: COR.texto }));
    else if (PALAVRAS.has(t)) saida.push(run(t, { color: COR.palavra, bold: true }));
    else saida.push(run(t));
  }
  if (comentario) saida.push(run(comentario, { color: COR.comentario, italics: true }));
  return saida;
}

function blocoDeCodigo(codigo, largura, tamanho = 18) {
  return new Table({
    columnWidths: [largura],
    width: { size: largura, type: WidthType.DXA },
    borders: {
      top: borda('C3C9D1', 6), bottom: borda('C3C9D1', 6),
      left: borda('C3C9D1', 6), right: borda('C3C9D1', 6),
      insideHorizontal: borda('FFFFFF', 0), insideVertical: borda('FFFFFF', 0),
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: largura, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: 'F4F5F7', color: 'auto' },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: codigo.split('\n').map((l) => new Paragraph({
          children: linhaDeCodigo(l, tamanho),
          spacing: { line: 240, after: 0 },
        })),
      })],
    })],
  });
}

// ── Figuras ─────────────────────────────────────────────────────────
function figura(arquivo, larguraCm) {
  const buf = fs.readFileSync(path.join(RAIZ, 'diagramas', arquivo));
  const w = buf.readUInt32BE(16);
  const h = buf.readUInt32BE(20);
  const px = (cm) => Math.round((cm / 2.54) * 96);
  return new Paragraph({
    children: [new ImageRun({
      type: 'png', data: buf,
      transformation: { width: px(larguraCm), height: px((h / w) * larguraCm) },
      altText: { title: arquivo, description: arquivo, name: arquivo },
    })],
    alignment: AlignmentType.CENTER,
    keepNext: true,
    spacing: { before: 0, after: 0 },
  });
}

// ── Renderização dos blocos de conteúdo ─────────────────────────────
function renderizar(blocos) {
  // Cada item: { paisagem: bool, filhos: [] } — uma seção do Word
  const secoes = [{ paisagem: false, filhos: [] }];
  const atual = () => secoes[secoes.length - 1];
  const cont = [0, 0, 0];

  blocos.forEach((b) => {
    if (b.paisagem && !atual().paisagem) secoes.push({ paisagem: true, filhos: [] });
    if (!b.paisagem && atual().paisagem) secoes.push({ paisagem: false, filhos: [] });
    const largura = atual().paisagem ? LARGURA_PAISAGEM : LARGURA_RETRATO;
    const f = atual().filhos;
    switch (b.t) {
      case 'h1': case 'h2': case 'h3': {
        const nivel = Number(b.t[1]);
        cont[nivel - 1] += 1;
        for (let k = nivel; k < 3; k++) cont[k] = 0;
        const numero = cont.slice(0, nivel).join('.');
        f.push(titulo(nivel, numero, b.texto));
        break;
      }
      case 'p': f.push(paragrafo(b.texto, b)); break;
      case 'alineas': f.push(...alineas(b.itens)); break;
      case 'figura':
        f.push(legendaTitulo('figura', b.numero, b.titulo));
        f.push(figura(b.arquivo, b.largura || 15.5));
        f.push(legendaFonte(textoDaFonte(b)));
        break;
      case 'quadro':
        f.push(legendaTitulo('quadro', b.numero, b.titulo));
        f.push(quadro(b, largura));
        f.push(legendaFonte(textoDaFonte(b)));
        break;
      case 'codigo':
        f.push(legendaTitulo('codigo', b.numero, b.titulo));
        f.push(blocoDeCodigo(b.codigo, largura));
        f.push(legendaFonte(textoDaFonte(b)));
        break;
      case 'referencias':
        f.push(tituloCentral('REFERÊNCIAS', true));
        b.itens.forEach((r) => f.push(new Paragraph({
          children: runs(r),
          alignment: AlignmentType.LEFT,
          spacing: { line: 240, after: 240 },
        })));
        break;
      case 'apendice':
        f.push(tituloCentral(b.titulo, true));
        if (b.texto) f.push(paragrafo(b.texto));
        f.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
        f.push(blocoDeCodigo(b.codigo, largura, 17));
        break;
      default: throw new Error('bloco desconhecido: ' + b.t);
    }
  });
  return secoes;
}

// ── Elementos pré-textuais ──────────────────────────────────────────
const { capa, resumo, siglas, blocos } = require('./conteudo')({ resultados, trecho });

function linhaCentral(texto, opcoes = {}) {
  return new Paragraph({
    children: runs(texto, { bold: opcoes.bold, size: opcoes.size || 24 }),
    alignment: AlignmentType.CENTER,
    spacing: { before: opcoes.before || 0, after: 0, line: 360 },
  });
}

const cidadeAno = () => [linhaCentral(capa.cidade, { bold: true }), linhaCentral(capa.ano, { bold: true })];

const paginaCapa = [
  linhaCentral(capa.instituicao, { bold: true }),
  linhaCentral(capa.curso),
  ...capa.autores.map((a, i) => linhaCentral(a, { before: i === 0 ? CM(3) : 0 })),
  linhaCentral(capa.titulo, { bold: true, before: CM(4.5) }),
];

const paginaRosto = [
  ...capa.autores.map((a) => linhaCentral(a)),
  linhaCentral(capa.titulo, { bold: true, before: CM(5) }),
  new Paragraph({
    children: runs(capa.natureza),
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: CM(8) },
    spacing: { before: CM(2.5), after: 0, line: 240 },
  }),
  new Paragraph({
    children: runs(capa.professor),
    alignment: AlignmentType.LEFT,
    indent: { left: CM(8) },
    spacing: { before: 240, after: 0, line: 240 },
  }),
];

const paginaResumo = [
  tituloCentral('RESUMO'),
  new Paragraph({
    children: runs(resumo.texto),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 360 },
  }),
  new Paragraph({
    children: runs(`**Palavras-chave:** ${resumo.palavras}`),
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 0 },
  }),
];

// Os blocos precisam ser numerados e renderizados antes das listas,
// porque as listas e o sumário são montados a partir deles.
numerar(blocos);
const secoesTexto = renderizar(blocos);

const pagina = (chave) => String(paginas[chave] || '0');

function entradaLista(texto) {
  return new Paragraph({
    children: [
      new TextRun({ text: texto, font: FONTE, size: 24 }),
      new TextRun({ text: '\t' + pagina(texto), font: FONTE, size: 24 }),
    ],
    tabStops: [{ type: TabStopType.RIGHT, position: LARGURA_RETRATO, leader: LeaderType.DOT }],
    indent: { left: CM(0.6), hanging: CM(0.6), right: CM(0.8) },
    spacing: { line: 360, after: 0 },
  });
}

function lista(titulo_, tipo) {
  return [tituloCentral(titulo_), ...legendas.filter((l) => l.tipo === tipo).map((l) => entradaLista(l.texto))];
}

const paginaSiglas = [
  tituloCentral('LISTA DE ABREVIATURAS E SIGLAS'),
  ...siglas.map(([sigla, significado]) => new Paragraph({
    children: [
      new TextRun({ text: sigla, font: FONTE, size: 24 }),
      new TextRun({ text: '\t' + significado, font: FONTE, size: 24 }),
    ],
    tabStops: [{ type: TabStopType.LEFT, position: CM(2.2) }],
    indent: { left: CM(2.2), hanging: CM(2.2) },
    spacing: { line: 360, after: 0 },
  })),
];

const sumario = [tituloCentral('SUMÁRIO')];
titulos.forEach((t) => {
  const chave = t.numero ? `${t.numero} ${t.texto}` : t.texto;
  const estilo = { font: FONTE, size: 24, bold: t.nivel === 0 || t.nivel === 1 || t.nivel === 3 };
  sumario.push(new Paragraph({
    children: t.numero
      ? [new TextRun({ text: t.numero, ...estilo }), new TextRun({ text: '\t' + t.texto, ...estilo }),
        new TextRun({ text: '\t' + pagina(chave), ...estilo })]
      : [new TextRun({ text: t.texto, ...estilo }), new TextRun({ text: '\t' + pagina(chave), ...estilo })],
    tabStops: [
      { type: TabStopType.LEFT, position: CM(1.4) },
      { type: TabStopType.RIGHT, position: LARGURA_RETRATO, leader: LeaderType.DOT },
    ],
    indent: t.numero ? { left: CM(1.4), hanging: CM(1.4), right: CM(0.8) } : { right: CM(0.8) },
    spacing: { line: 360, after: 0 },
  }));
});

const listas = [
  ...lista('LISTA DE FIGURAS', 'figura'),
  ...lista('LISTA DE QUADROS', 'quadro'),
  ...lista('LISTA DE CÓDIGOS', 'codigo'),
];

fs.writeFileSync(path.join(AQUI, 'alvos.json'), JSON.stringify(ordem, null, 1));

// ── Documento ───────────────────────────────────────────────────────
const MARGENS = { top: CM(3), left: CM(3), bottom: CM(2), right: CM(2), header: CM(2), footer: CM(2) };
const vazio = () => new Paragraph({ children: [] });
const cabecalhoVazio = () => new Header({ children: [vazio()] });
const rodapeVazio = () => new Footer({ children: [vazio()] });
const cabecalhoPagina = () => new Header({
  children: [new Paragraph({
    alignment: AlignmentType.RIGHT,
    children: [new TextRun({ children: [PageNumber.CURRENT], font: FONTE, size: 20 })],
  })],
});

const secoesWord = [
  {
    properties: { page: { margin: MARGENS } },
    headers: { default: cabecalhoVazio() },
    footers: { default: new Footer({ children: cidadeAno() }) },
    children: paginaCapa,
  },
  {
    properties: { page: { margin: MARGENS, pageNumbers: { start: 1 } }, titlePage: true },
    headers: { default: cabecalhoVazio(), first: cabecalhoVazio() },
    footers: { default: rodapeVazio(), first: new Footer({ children: cidadeAno() }) },
    children: [...paginaRosto, ...paginaResumo, ...listas, ...paginaSiglas, ...sumario],
  },
  ...secoesTexto.map((s) => ({
    properties: {
      page: {
        margin: MARGENS,
        size: s.paisagem ? { orientation: PageOrientation.LANDSCAPE } : undefined,
      },
    },
    headers: { default: cabecalhoPagina() },
    footers: { default: rodapeVazio() },
    children: s.filhos,
  })),
];

const doc = new Document({
  creator: 'Grupo — Banco de Dados',
  title: capa.tituloSimples,
  description: 'Documentação da implementação do banco de dados de uma concessionária de veículos',
  styles: {
    default: {
      document: { run: { font: FONTE, size: 24 } },
      heading1: { run: { font: FONTE, size: 24, bold: true, color: '000000' } },
      heading2: { run: { font: FONTE, size: 24, bold: false, color: '000000' } },
      heading3: { run: { font: FONTE, size: 24, bold: true, color: '000000' } },
    },
  },
  sections: secoesWord,
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(SAIDA, buf);
  console.log('gerado:', path.relative(process.cwd(), SAIDA));
});
