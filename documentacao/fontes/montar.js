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

const { capa, historico, secoes, casosDeUso } = require('./conteudo');
const { ferramentas, telas } = require('./conteudo2');
const { acessibilidade, arquitetura, api, testes, conclusao, cronograma, referencias } = require('./conteudo3');
const { requisitosFuncionais, requisitosNaoFuncionais } = require('./requisitos');
const { modeloEntidadeRelacionamento, relacionamentos, implementacoesBanco } = require('./banco');
const { dicionario, relacoes, enumerados } = require('./banco_gerado');

const TELAS_DIR = path.join(__dirname, 'telas');
const DIAGRAMAS_DIR = path.join(__dirname, 'diagramas');
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
function imagemDiagrama(arquivo) {
  return imagem(path.join(DIAGRAMAS_DIR, arquivo), arquivo);
}

function imagemTela(arquivo) {
  return imagem(path.join(TELAS_DIR, arquivo), arquivo);
}

function imagem(caminho, arquivo) {
  if (!fs.existsSync(caminho)) throw new Error('imagem não encontrada: ' + arquivo);
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
      tableHeader: i === 0 && !opcoes.semCabecalho,
      children: linha.map((celula, j) => new TableCell({
        width: { size: colunas[j], type: WidthType.DXA },
        shading: (i === 0 && !opcoes.semCabecalho) ? { type: ShadingType.CLEAR, fill: 'E8EEF0' } : undefined,
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: [new TextRun({
            text: celula, font: FONTE, size: fonte,
            bold: i === 0 || (opcoes.rotuloNegrito && j === 0),
          })],
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

// Histórico de revisões, entre a capa e o sumário, como no modelo
filhos.push(new Paragraph({
  children: [new TextRun({ text: 'HISTÓRICO DE REVISÕES', font: FONTE, size: 24, bold: true })],
  alignment: AlignmentType.CENTER, spacing: { after: 360, line: 360 },
}));
filhos.push(tabela(historico, [0.8, 0.55, 2.4, 2.2], { fonte: 18 }));
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

/* Um requisito vira uma tabela de duas colunas: rótulo à esquerda, em
   negrito, e o conteúdo à direita — os mesmos campos do modelo. */
function blocoRequisito(r) {
  const linhas = [
    ['IDENTIFICAÇÃO', r.id],
    ['NOME', r.nome],
  ];
  if (r.atores) linhas.push(['ATORES', r.atores]);
  linhas.push(['PRIORIDADE', r.prioridade]);
  linhas.push(['DESCRIÇÃO', r.descricao]);
  if (r.entradas) linhas.push(['ENTRADAS E PRÉ-CONDIÇÕES', r.entradas]);
  if (r.saidas) linhas.push(['SAÍDAS E PÓS-CONDIÇÕES', r.saidas]);
  if (r.verificacao) linhas.push(['COMO É VERIFICADO', r.verificacao]);
  return tabela(linhas, [1, 2.6], { rotuloNegrito: true });
}
const espaco = () => new Paragraph({ spacing: { after: 240 }, children: [] });

// Seção 9 — requisitos funcionais
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('9', 'REQUISITOS FUNCIONAIS'));
filhos.push(corpo('Os requisitos funcionais descrevem o que o sistema faz. Cada um corresponde a uma funcionalidade já implementada e coberta por testes automatizados, e está escrito do ponto de vista de quem usa, não de quem programa.'));
filhos.push(corpo(`São ${requisitosFuncionais.length} requisitos, agrupados na ordem em que as pessoas encontram o sistema: primeiro a estrutura do condomínio e o acesso, depois a convivência, a portaria e o financeiro.`));
requisitosFuncionais.forEach((r) => {
  filhos.push(blocoRequisito(r));
  filhos.push(espaco());
});

// Seção 10 — requisitos não funcionais
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('10', 'REQUISITOS NÃO FUNCIONAIS'));
filhos.push(corpo('Os requisitos não funcionais descrevem como o sistema se comporta: com que qualidade, segurança e desempenho as funcionalidades são entregues. Ao contrário dos funcionais, não correspondem a uma tela ou a um botão, mas valem para o sistema inteiro.'));
filhos.push(corpo('Cada bloco traz, além da descrição, a forma como o requisito é verificado. Um requisito não funcional que não se consegue verificar é apenas uma intenção.'));
requisitosNaoFuncionais.forEach((g) => {
  filhos.push(titulo2(g.n, g.grupo));
  g.itens.forEach((r) => {
    filhos.push(blocoRequisito(r));
    filhos.push(espaco());
  });
});

// Seção 11 — diagrama de casos de uso
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('11', 'DIAGRAMA DE CASO DE USO'));
filhos.push(corpo('O diagrama de casos de uso, da UML, mostra quem usa o sistema e para quê. Os bonecos são os atores — os quatro papéis de usuário —, as elipses são os casos de uso, e cada linha indica que o ator participa daquele caso. Tudo o que está dentro do retângulo é responsabilidade do SmartCondo; os atores ficam do lado de fora.'));
filhos.push(corpo('Os casos do administrador e do síndico estão à esquerda e os do porteiro e do morador à direita, na mesma posição dos seus atores, para que as linhas quase não se cruzem. Autenticar-se e recuperar a senha ligam-se aos quatro atores porque valem para qualquer um deles.'));
filhos.push(imagemDiagrama('casos_de_uso.png'));
filhos.push(legenda('Figura — Diagrama de casos de uso do SmartCondo'));

// Seção 12 — casos de uso
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('12', 'CASOS DE USO'));
filhos.push(corpo('Os casos de uso a seguir detalham as principais interações do diagrama anterior, indicando o usuário responsável, o resumo da operação e a sequência de ações de cada lado. A numeração das ações mostra a ordem em que acontecem, alternando entre o usuário e o sistema.'));
casosDeUso.forEach((caso, i) => {
  filhos.push(titulo2(`12.${i + 1}`, `UC ${caso.nome}`));
  filhos.push(corpoComTermo('Usuário principal:', `Usuário principal: ${caso.principal}`));
  filhos.push(corpoComTermo('Resumo:', `Resumo: ${caso.resumo}`));
  if (caso.prerequisitos) {
    filhos.push(corpoComTermo('Pré-requisitos:', `Pré-requisitos: ${caso.prerequisitos}`));
  }
  filhos.push(tabelaCasoDeUso(caso));
  if (caso.nota) filhos.push(corpo(caso.nota, { after: 300 }));
  else filhos.push(espaco());
});

// Seção 13 — prototipação
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('13', 'PROTOTIPAÇÃO DAS TELAS'));
filhos.push(corpo('As telas a seguir foram capturadas do sistema em funcionamento, com dados reais vindos da API e do banco de dados.'));
telas.forEach((t) => {
  // As telas foram escritas com a numeração antiga (11.x); aqui passam a 13.x.
  const n = t.n.replace(/^11\./, '13.');
  const nivel = n.split('.').length;
  filhos.push(nivel === 2 ? titulo2(n, t.titulo) : titulo3(n, t.titulo));
  if (t.texto) filhos.push(corpo(t.texto));
  if (t.imagem) {
    filhos.push(imagemTela(t.imagem));
    filhos.push(legenda(`Figura — ${t.legenda}`));
  }
});

// Seção 14 — modelo entidade-relacionamento
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('14', 'MODELO ENTIDADE-RELACIONAMENTO'));
modeloEntidadeRelacionamento.paragrafos.forEach((p) => filhos.push(corpo(p)));
const totalColunas = dicionario.reduce((s, t) => s + t.colunas.length, 0);
filhos.push(corpo(`Ao todo são ${dicionario.length} entidades, ${totalColunas} atributos e ${relacoes.length} relacionamentos. O quadro abaixo resume o papel de cada entidade; o detalhe de cada atributo está no dicionário de dados.`));
filhos.push(tabela(
  [['Entidade', 'O que representa'], ...dicionario.map((t) => [t.nome, t.resumo])],
  [1, 2.6]));
filhos.push(legenda('Quadro — Entidades do banco de dados do SmartCondo'));

// Seção 15 — diagrama entidade-relacionamento
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('15', 'DIAGRAMA ENTIDADE-RELACIONAMENTO'));
filhos.push(corpo('O diagrama entidade-relacionamento mostra as tabelas do banco e como elas se ligam. É gerado diretamente do banco em funcionamento — colunas, tipos e chaves são lidos do catálogo do PostgreSQL —, de modo que a figura não fica defasada quando a estrutura muda.'));
filhos.push(corpo('Vinte entidades com mais de duzentos atributos não cabem legíveis numa página só. Por isso o diagrama vem em quatro partes: uma visão de conjunto, com os nomes e as ligações, e três recortes por assunto, com todos os atributos. Nos recortes, PK marca a chave primária e FK as chaves estrangeiras; as setas partem da entidade que guarda a chave estrangeira e apontam para a entidade referenciada.'));
filhos.push(imagemDiagrama('der_geral.png'));
filhos.push(legenda('Figura — Diagrama entidade-relacionamento: visão de conjunto'));
[
  ['der_1.png', 'núcleo — condomínio, unidades e usuários'],
  ['der_2.png', 'convivência — espaços, comunicados, documentos e ocorrências'],
  ['der_3.png', 'financeiro e portaria'],
].forEach(([arquivo, nome]) => {
  filhos.push(imagemDiagrama(arquivo));
  filhos.push(legenda(`Figura — Diagrama entidade-relacionamento: ${nome}`));
});

// Seção 16 — relacionamentos
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('16', 'RELACIONAMENTOS'));
relacionamentos.paragrafos.forEach((p) => filhos.push(corpo(p)));
filhos.push(tabela(
  [['Entidade', 'Chave estrangeira', 'Referencia', 'Significado'],
   ...relacoes.map((r) => [r.origem, r.coluna, r.destino, r.texto || `Cada registro de ${r.origem} pertence a um registro de ${r.destino}`])],
  [3.5, 2.9, 2.5, 7.1], { fonte: 17 }));
filhos.push(legenda('Quadro — Relacionamentos entre as entidades'));

// Seção 17 — dicionário de dados
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('17', 'DICIONÁRIO DE DADOS'));
filhos.push(corpo('O dicionário de dados descreve cada atributo de cada entidade: o nome da coluna, o tipo, se o preenchimento é obrigatório, se é chave e o que significa. Assim como o diagrama, é gerado a partir do banco em funcionamento, para que tipo e obrigatoriedade nunca divirjam do que está gravado.'));
filhos.push(corpo('Nos tipos, VARCHAR(n) é texto de até n caracteres, NUMERIC(10,2) é valor com duas casas decimais, DATE é data, TIME é hora, TIMESTAMPTZ é data e hora com fuso horário e BOOLEAN é sim ou não. ENUM indica um tipo enumerado: a coluna só aceita os valores listados na sua descrição, e o nome do tipo aparece junto, para consulta no quadro de tipos enumerados da seção 18.'));
dicionario.forEach((t, i) => {
  filhos.push(titulo2(`17.${i + 1}`, t.nome));
  filhos.push(corpo(t.resumo));
  filhos.push(tabela(
    [['Coluna', 'Tipo', 'Obrig.', 'Chave', 'Descrição'],
     ...t.colunas.map((c) => [c.coluna, c.tipo, c.obrigatorio, c.chave, c.descricao])],
    [3.5, 2.6, 1.15, 1.3, 7.45], { fonte: 17 }));
  filhos.push(legenda(`Quadro — Dicionário de dados da tabela ${t.nome}`));
});

// Seção 18 — implementações no banco
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('18', 'IMPLEMENTAÇÕES NO BANCO DE DADOS'));
implementacoesBanco.paragrafos.forEach((p) => filhos.push(corpo(p)));
implementacoesBanco.subsecoes.forEach((s, i) => {
  filhos.push(titulo2(`18.${i + 1}`, s.nome));
  s.paragrafos.forEach((p) => filhos.push(corpo(p)));
});
filhos.push(corpo('O quadro a seguir reúne os tipos enumerados declarados no banco e os valores aceitos por cada um.'));
filhos.push(tabela(
  [['Tipo enumerado', 'Valores aceitos'], ...enumerados.map((e) => [e.nome, e.valores])],
  [1, 2.2], { fonte: 18 }));
filhos.push(legenda('Quadro — Tipos enumerados do banco de dados'));

// Seção 19 — linguagens e ferramentas
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('19', 'LINGUAGENS E FERRAMENTAS UTILIZADAS'));
filhos.push(corpo(ferramentas.intro));
ferramentas.itens.forEach((f) => {
  filhos.push(titulo2(f.n.replace(/^10\./, '19.'), f.nome));
  filhos.push(corpo(f.texto));
});

// Seção 20 — arquitetura. A modelagem do banco, que antes ficava aqui,
// ganhou as seções 14 a 18; fica a visão das camadas e a segurança.
filhos.push(titulo1('20', 'ARQUITETURA DO SISTEMA'));
arquitetura.paragrafos.forEach((p) => filhos.push(corpo(p)));
arquitetura.subsecoes
  .filter((s) => !/^Modelagem/.test(s.nome))
  .forEach((s, i) => {
    filhos.push(titulo2(`20.${i + 1}`, s.nome));
    s.paragrafos.forEach((p) => filhos.push(corpo(p)));
  });

// Seção 21 — API
filhos.push(titulo1('21', 'API REST'));
api.paragrafos.forEach((p) => filhos.push(corpo(p)));
filhos.push(tabela(api.tabela, [1.1, 0.6, 3]));
filhos.push(legenda('Quadro — Módulos da API e suas responsabilidades'));

// Seção 22 — acessibilidade
filhos.push(new Paragraph({ children: [new PageBreak()] }));
filhos.push(titulo1('22', 'ACESSIBILIDADE'));
filhos.push(corpo(acessibilidade.intro));
acessibilidade.itens.forEach((a) => {
  filhos.push(titulo2(a.n.replace(/^12\./, '22.'), a.nome));
  a.paragrafos.forEach((p) => filhos.push(corpo(p)));
});

// Seção 23 — testes
filhos.push(titulo1('23', 'TESTES AUTOMATIZADOS'));
testes.paragrafos.forEach((p) => filhos.push(corpo(p)));
filhos.push(tabela(testes.tabela, [1.4, 0.6, 3]));
filhos.push(legenda('Quadro — Distribuição dos casos de teste'));

// Seção 24 — conclusão
filhos.push(titulo1('24', 'CONCLUSÃO'));
conclusao.forEach((p) => filhos.push(corpo(p)));

// Seção 25 — cronograma, numa seção em paisagem. Em retrato, as seis
// colunas ficam com 2,5 cm e palavras como "Desenvolvimento" estouram a
// célula; deitada, a página oferece 24,7 cm de largura útil.
const LARGURA_PAISAGEM = CM(24.7);
const cronogramaFilhos = [
  titulo1('25', 'CRONOGRAMA EM FASES'),
  tabela(cronograma, [0.7, 1, 1, 1, 1, 1], { largura: LARGURA_PAISAGEM, fonte: 18 }),
  legenda('Quadro — Cronograma do projeto'),
];

// Seção 26 — referências, de volta ao retrato
const referenciasFilhos = [titulo1('26', 'REFERÊNCIA BIBLIOGRÁFICA')];
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
  // Ao abrir, o Word pergunta se deve atualizar os campos — e com isso
  // monta o sumário com os números de página, sem ninguém precisar
  // lembrar do "Atualizar campo".
  features: { updateFields: true },
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
