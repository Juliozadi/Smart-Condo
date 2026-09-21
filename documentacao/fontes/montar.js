/* Monta a documentação do SmartCondo em .docx, seguindo a ABNT:
 * Arial 12, entrelinhas 1,5, texto justificado, recuo de 1,25 cm na
 * primeira linha, margens 3 cm (esquerda/superior) e 2 cm
 * (direita/inferior), e numeração de página no canto superior direito. */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, TabStopType,
  PageBreak, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, Header, PageNumber, TableOfContents, convertMillimetersToTwip,
  LevelFormat, VerticalAlign, PageOrientation,
} = require('docx');

const { capa, secoes, casosDeUso } = require('./conteudo');
const { ferramentas, telas } = require('./conteudo2');
const { acessibilidade, arquitetura, api, testes, conclusao, cronograma, referencias } = require('./conteudo3');

const TELAS_DIR = path.join(__dirname, 'telas');
const FONTE = 'Arial';
const CM = (n) => convertMillimetersToTwip(n * 10);
const RECUO = CM(1.25);
// Largura útil da página: 21 cm - 3 cm - 2 cm = 16 cm
const LARGURA_UTIL = CM(16);

// ── Blocos de texto ─────────────────────────────────────────────────
function corpo(texto, opcoes = {}) {
  return new Paragraph({
    children: [new TextRun({ text: texto, font: FONTE, size: 24 })],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: opcoes.after === undefined ? 120 : opcoes.after },
    indent: { firstLine: opcoes.semRecuo ? 0 : RECUO },
  });
}

/* Parágrafo que começa com um termo em negrito, como "Porteiro: ..." */
function corpoComTermo(termo, texto) {
  const resto = texto.slice(termo.length);
  return new Paragraph({
    children: [
      new TextRun({ text: termo, font: FONTE, size: 24, bold: true }),
      new TextRun({ text: resto, font: FONTE, size: 24 }),
    ],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 120 },
    indent: { firstLine: RECUO },
  });
}

function titulo1(numero, texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: `${numero} ${texto}`, font: FONTE, size: 24, bold: true })],
    spacing: { before: 360, after: 240, line: 360 },
    alignment: AlignmentType.LEFT,
  });
}

function titulo2(numero, texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text: `${numero} ${texto}`, font: FONTE, size: 24, bold: true })],
    spacing: { before: 280, after: 160, line: 360 },
    alignment: AlignmentType.LEFT,
  });
}

function titulo3(numero, texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text: `${numero} ${texto}`, font: FONTE, size: 24 })],
    spacing: { before: 240, after: 140, line: 360 },
    alignment: AlignmentType.LEFT,
  });
}

function legenda(texto) {
  return new Paragraph({
    children: [new TextRun({ text: texto, font: FONTE, size: 20 })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 240, line: 240 },
  });
}

function marcador(texto) {
  return new Paragraph({
    children: [new TextRun({ text: texto, font: FONTE, size: 24 })],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 60 },
    numbering: { reference: 'lista-pontos', level: 0 },
  });
}

// ── Imagem das telas ────────────────────────────────────────────────
function imagemTela(arquivo) {
  const caminho = path.join(TELAS_DIR, arquivo);
  if (!fs.existsSync(caminho)) throw new Error('print não encontrado: ' + arquivo);
  const { width, height } = tamanhoPng(caminho);
  // Cabe na largura útil (16 cm) e nunca passa de 17 cm de altura, para
  // a imagem e a legenda ficarem na mesma página.
  const maxLargura = 15.5, maxAltura = 17;
  let larguraCm = maxLargura;
  let alturaCm = (height / width) * larguraCm;
  if (alturaCm > maxAltura) {
    alturaCm = maxAltura;
    larguraCm = (width / height) * alturaCm;
  }
  // O docx-js recebe a medida em pixels e converte a 96 dpi.
  const paraPx = (cm) => Math.round((cm / 2.54) * 96);
  return new Paragraph({
    children: [new ImageRun({
      type: 'png',
      data: fs.readFileSync(caminho),
      transformation: { width: paraPx(larguraCm), height: paraPx(alturaCm) },
    })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 0 },
  });
}

/* Lê largura e altura direto do cabeçalho IHDR do PNG. */
function tamanhoPng(caminho) {
  const buf = fs.readFileSync(caminho);
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

// ── Tabelas ─────────────────────────────────────────────────────────
function tabela(linhas, larguras, opcoes = {}) {
  const util = opcoes.largura || LARGURA_UTIL;
  const fonte = opcoes.fonte || 20;
  const total = larguras.reduce((a, b) => a + b, 0);
  const colunas = larguras.map((f) => Math.round((f / total) * util));
  return new Table({
    columnWidths: colunas,
    width: { size: util, type: WidthType.DXA },
    rows: linhas.map((linha, i) => new TableRow({
      tableHeader: i === 0,
      children: linha.map((celula, j) => new TableCell({
        width: { size: colunas[j], type: WidthType.DXA },
        shading: i === 0 ? { type: ShadingType.CLEAR, fill: 'E8EEF0' } : undefined,
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: [new TextRun({ text: celula, font: FONTE, size: fonte, bold: i === 0 })],
          alignment: j === 0 || i === 0 ? AlignmentType.LEFT : AlignmentType.LEFT,
          spacing: { line: 240, after: 0 },
        })],
      })),
    })),
  });
}

/* Tabela de duas colunas de um caso de uso, como no documento original. */
function tabelaCasoDeUso(caso) {
  const maior = Math.max(caso.sistema.length, caso.usuario.length);
  const linhas = [['Ações do sistema', 'Ações do usuário']];
  for (let i = 0; i < maior; i++) {
    linhas.push([caso.sistema[i] || '', caso.usuario[i] || '']);
  }
  return tabela(linhas, [1, 1]);
}

// ── Documento ───────────────────────────────────────────────────────
const filhos = [];

// Capa
filhos.push(new Paragraph({ spacing: { before: CM(4) }, children: [] }));
filhos.push(new Paragraph({
  children: [new TextRun({ text: capa.titulo, font: FONTE, size: 32, bold: true })],
  alignment: AlignmentType.CENTER, spacing: { after: 600, line: 360 },
}));
filhos.push(new Paragraph({
  children: [new TextRun({ text: 'Integrantes:', font: FONTE, size: 24, bold: true })],
  alignment: AlignmentType.CENTER, spacing: { after: 160, line: 360 },
}));
capa.integrantes.forEach((nome) => filhos.push(new Paragraph({
  children: [new TextRun({ text: nome, font: FONTE, size: 24 })],
  alignment: AlignmentType.CENTER, spacing: { after: 60, line: 360 },
})));
filhos.push(new Paragraph({ spacing: { before: CM(5) }, children: [] }));
filhos.push(new Paragraph({
  children: [new TextRun({ text: capa.disciplina, font: FONTE, size: 24, bold: true })],
  alignment: AlignmentType.CENTER, spacing: { after: 60, line: 360 },
}));
filhos.push(new Paragraph({
  children: [new TextRun({ text: capa.ano, font: FONTE, size: 24 })],
  alignment: AlignmentType.CENTER, spacing: { after: 0, line: 360 },
}));
filhos.push(new Paragraph({ children: [new PageBreak()] }));

// Sumário automático
filhos.push(new Paragraph({
  children: [new TextRun({ text: 'SUMÁRIO', font: FONTE, size: 24, bold: true })],
  alignment: AlignmentType.CENTER, spacing: { after: 360, line: 360 },
}));
filhos.push(new TableOfContents('Sumário', { hyperlink: true, headingStyleRange: '1-3' }));
filhos.push(new Paragraph({ children: [new PageBreak()] }));

// Seções 1 a 8
secoes.forEach((s) => {
  filhos.push(titulo1(s.n, s.titulo));
  s.paragrafos.forEach((p) => {
    if (typeof p === 'string') filhos.push(corpo(p));
    else filhos.push(corpoComTermo(p.negritoAte, p.texto));
  });
});

// Seção 9 — casos de uso
filhos.push(titulo1('9', 'REQUISITOS FUNCIONAIS E NÃO FUNCIONAIS'));
filhos.push(corpo('Os casos de uso a seguir descrevem as principais interações entre os usuários e o sistema, indicando o usuário responsável, o resumo da operação e a sequência de ações de cada lado.'));
casosDeUso.forEach((caso) => {
  filhos.push(corpoComTermo('Nome do caso de uso:', `Nome do caso de uso: ${caso.nome}`));
  filhos.push(corpoComTermo('Usuário principal:', `Usuário principal: ${caso.principal}`));
  filhos.push(corpoComTermo('Resumo:', `Resumo: ${caso.resumo}`));
  if (caso.prerequisitos) {
    filhos.push(corpoComTermo('Pré-requisitos:', `Pré-requisitos: ${caso.prerequisitos}`));
  }
  filhos.push(tabelaCasoDeUso(caso));
  if (caso.nota) filhos.push(corpo(caso.nota, { after: 300 }));
  else filhos.push(new Paragraph({ spacing: { after: 240 }, children: [] }));
});

// Seção 10 — linguagens e ferramentas
filhos.push(titulo1('10', 'LINGUAGENS E FERRAMENTAS UTILIZADAS'));
filhos.push(corpo(ferramentas.intro));
ferramentas.itens.forEach((f) => {
  filhos.push(titulo2(f.n, f.nome));
  filhos.push(corpo(f.texto));
});

// Seção 11 — prototipação
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('11', 'PROTOTIPAÇÃO DAS TELAS'));
filhos.push(corpo('As telas a seguir foram capturadas do sistema em funcionamento, com dados reais vindos da API e do banco de dados.'));
telas.forEach((t) => {
  const nivel = t.n.split('.').length;
  filhos.push(nivel === 2 ? titulo2(t.n, t.titulo) : titulo3(t.n, t.titulo));
  if (t.texto) filhos.push(corpo(t.texto));
  if (t.imagem) {
    filhos.push(imagemTela(t.imagem));
    filhos.push(legenda(`Figura — ${t.legenda}`));
  }
});

// Seção 12 — acessibilidade
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('12', 'ACESSIBILIDADE'));
filhos.push(corpo(acessibilidade.intro));
acessibilidade.itens.forEach((a) => {
  filhos.push(titulo2(a.n, a.nome));
  a.paragrafos.forEach((p) => filhos.push(corpo(p)));
});

// Seção 13 — arquitetura e banco
filhos.push(titulo1('13', 'ARQUITETURA E BANCO DE DADOS'));
arquitetura.paragrafos.forEach((p) => filhos.push(corpo(p)));
arquitetura.subsecoes.forEach((s) => {
  filhos.push(titulo2(s.n, s.nome));
  s.paragrafos.forEach((p) => filhos.push(corpo(p)));
  if (s.tabela) {
    filhos.push(tabela(s.tabela, [1, 2]));
    filhos.push(legenda('Quadro — Tabelas do banco de dados do SmartCondo'));
  }
});

// Seção 14 — API
filhos.push(titulo1('14', 'API REST'));
api.paragrafos.forEach((p) => filhos.push(corpo(p)));
filhos.push(tabela(api.tabela, [1.1, 0.6, 3]));
filhos.push(legenda('Quadro — Módulos da API e suas responsabilidades'));

// Seção 15 — testes
filhos.push(titulo1('15', 'TESTES AUTOMATIZADOS'));
testes.paragrafos.forEach((p) => filhos.push(corpo(p)));
filhos.push(tabela(testes.tabela, [1.4, 0.6, 3]));
filhos.push(legenda('Quadro — Distribuição dos casos de teste'));

// Seção 16 — conclusão
filhos.push(titulo1('16', 'CONCLUSÃO'));
conclusao.forEach((p) => filhos.push(corpo(p)));

// Seção 17 — cronograma, numa seção em paisagem. Em retrato, as seis
// colunas ficam com 2,5 cm e palavras como "Desenvolvimento" estouram a
// célula; deitada, a página oferece 24,7 cm de largura útil.
const LARGURA_PAISAGEM = CM(24.7);
const cronogramaFilhos = [
  titulo1('17', 'CRONOGRAMA EM FASES'),
  tabela(cronograma, [0.7, 1, 1, 1, 1, 1], { largura: LARGURA_PAISAGEM, fonte: 18 }),
  legenda('Quadro — Cronograma do projeto'),
];

// Seção 18 — referências, de volta ao retrato
const referenciasFilhos = [titulo1('18', 'REFERÊNCIA BIBLIOGRÁFICA')];
referencias.forEach((r) => referenciasFilhos.push(new Paragraph({
  children: [new TextRun({ text: r, font: FONTE, size: 24 })],
  alignment: AlignmentType.LEFT,
  spacing: { line: 240, after: 240 },
})));

const MARGENS = { top: CM(3), left: CM(3), bottom: CM(2), right: CM(2) };
const numeroDaPagina = () => new Header({
  children: [new Paragraph({
    alignment: AlignmentType.RIGHT,
    children: [new TextRun({ children: [PageNumber.CURRENT], font: FONTE, size: 20 })],
  })],
});

const doc = new Document({
  creator: 'Projeto Integrador I — SmartCondo',
  title: 'Sistema de Gerenciamento de Condomínios',
  description: 'Documentação do projeto SmartCondo',
  numbering: {
    config: [{
      reference: 'lista-pontos',
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: '•',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: CM(1.25), hanging: CM(0.5) } } },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: FONTE, size: 24 } },
      heading1: { run: { font: FONTE, size: 24, bold: true, color: '000000' } },
      heading2: { run: { font: FONTE, size: 24, bold: true, color: '000000' } },
      heading3: { run: { font: FONTE, size: 24, bold: false, color: '000000' } },
    },
  },
  sections: [
    { properties: { page: { margin: MARGENS } }, headers: { default: numeroDaPagina() }, children: filhos },
    {
      properties: {
        page: {
          margin: MARGENS,
          // Em paisagem o docx-js troca largura e altura sozinho.
          size: { orientation: PageOrientation.LANDSCAPE },
        },
      },
      headers: { default: numeroDaPagina() },
      children: cronogramaFilhos,
    },
    { properties: { page: { margin: MARGENS } }, headers: { default: numeroDaPagina() }, children: referenciasFilhos },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const saida = path.join(__dirname, 'DocumentacaoSmartCondo.docx');
  fs.writeFileSync(saida, buf);
  console.log('gerado:', saida, '|', (buf.length / 1024 / 1024).toFixed(1), 'MB');
});
