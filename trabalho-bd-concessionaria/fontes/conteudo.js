/* Conteúdo da documentação: capa, resumo, siglas e as seções do texto.
 *
 * Marcação nos textos: **negrito**, *itálico*, `código`, ==destaque==
 * (fundo amarelo: campo que o grupo precisa preencher) e referências
 * {F:id}, {Q:id}, {C:id}, trocadas por "Figura n", "Quadro n", "Código n".
 *
 * O código SQL vem do próprio script (função trecho) e as saídas vêm de
 * resultados.json, gravado pelo coletar_resultados.py a partir de uma
 * execução real no MySQL.
 */
module.exports = ({ resultados, trecho }) => {
  const r = (nome) => ({
    cabecalho: resultados[nome].colunas,
    linhas: resultados[nome].linhas,
  });
  const versao = resultados.versao.split('-')[0];

  const capa = {
    instituicao: '==[NOME DA INSTITUIÇÃO]==',
    curso: '==[NOME DO CURSO]==',
    autores: [
      '==[NOME COMPLETO DO INTEGRANTE 1]==',
      '==[NOME COMPLETO DO INTEGRANTE 2]==',
      '==[NOME COMPLETO DO INTEGRANTE 3]==',
      '==[NOME COMPLETO DO INTEGRANTE 4]==',
    ],
    titulo: 'BANCO DE DADOS DE UMA CONCESSIONÁRIA DE VEÍCULOS: modelagem e implementação em MySQL',
    tituloSimples: 'Banco de dados de uma concessionária de veículos',
    natureza: 'Trabalho apresentado à disciplina de ==[NOME DA DISCIPLINA]== do curso de ==[NOME DO CURSO]== da ==[NOME DA INSTITUIÇÃO]==, como requisito parcial para avaliação.',
    professor: 'Professor: Odirley Franco',
    cidade: '==[CIDADE]==',
    ano: '2026',
  };

  const resumo = {
    texto: 'Este trabalho apresenta a implementação básica de um banco de dados relacional para um sistema de gestão de uma concessionária de veículos, que controla o cadastro de fornecedores, veículos, clientes e funcionários e o registro das vendas. Foi escolhido o Sistema Gerenciador de Banco de Dados (SGBD) MySQL 8.0, por ser gratuito, amplamente utilizado e oferecer, com o motor InnoDB, transações, chaves estrangeiras e restrições de verificação. A modelagem foi desenvolvida em dois níveis: o Modelo Entidade-Relacionamento (MER), conceitual, e o Diagrama Entidade-Relacionamento (DER), lógico, complementados por um dicionário de dados. Em seguida, foram criados o banco de dados e a estrutura de cinco tabelas com comandos da linguagem de definição de dados, e realizada a carga de dados com os comandos INSERT, UPDATE e DELETE. Todos os comandos foram executados no MySQL ' + versao + ', e testes de integridade confirmaram que o SGBD recusa operações que deixariam os dados inconsistentes, como vender duas vezes o mesmo veículo ou excluir um cliente que possui compras registradas.',
    palavras: 'Banco de dados. MySQL. Modelagem de dados. SQL. Concessionária de veículos.',
  };

  const siglas = [
    ['ABNT', 'Associação Brasileira de Normas Técnicas'],
    ['ACID', 'Atomicidade, Consistência, Isolamento e Durabilidade'],
    ['CNPJ', 'Cadastro Nacional da Pessoa Jurídica'],
    ['CPF', 'Cadastro de Pessoas Físicas'],
    ['DDL', 'Data Definition Language (Linguagem de Definição de Dados)'],
    ['DER', 'Diagrama Entidade-Relacionamento'],
    ['DML', 'Data Manipulation Language (Linguagem de Manipulação de Dados)'],
    ['DQL', 'Data Query Language (Linguagem de Consulta de Dados)'],
    ['FK', 'Foreign Key (chave estrangeira)'],
    ['MER', 'Modelo Entidade-Relacionamento'],
    ['PK', 'Primary Key (chave primária)'],
    ['SGBD', 'Sistema Gerenciador de Banco de Dados'],
    ['SQL', 'Structured Query Language (Linguagem de Consulta Estruturada)'],
    ['TCL', 'Transaction Control Language (Linguagem de Controle de Transações)'],
    ['UK', 'Unique Key (chave única)'],
  ];

  const dicionario = (tabela, linhas) => ({
    t: 'quadro', id: `dic_${tabela}`, titulo: `Dicionário de dados da tabela ${tabela}`,
    cabecalho: ['Coluna', 'Tipo', 'Nulo', 'Chave', 'Padrão / Restrição', 'Descrição'],
    larguras: [2.7, 2.75, 1.15, 1.35, 3.6, 4.45],
    fonte: 18,
    linhas,
  });

  const blocos = [
    // ── 1 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Introdução' },
    { t: 'p', texto: 'Uma concessionária de veículos lida diariamente com um grande volume de informações: os veículos que chegam dos fornecedores, os que estão em estoque, reservados ou já vendidos, os dados dos clientes, a equipe de vendas e o histórico de cada negociação. Quando essas informações ficam espalhadas em planilhas ou anotações, surgem problemas conhecidos, como o mesmo veículo vendido duas vezes, cadastros de clientes duplicados e a dificuldade de saber quanto cada vendedor negociou no mês.' },
    { t: 'p', texto: 'Um banco de dados relacional resolve esses problemas ao reunir as informações em um único lugar, organizadas em tabelas relacionadas entre si, e ao entregar a um Sistema Gerenciador de Banco de Dados (SGBD) a tarefa de fazer cumprir as regras do negócio. Segundo Elmasri e Navathe (2018), o SGBD é um conjunto de programas que permite aos usuários criar e manter um banco de dados, facilitando a definição, a construção, a manipulação e o compartilhamento dos dados entre diversos usuários e aplicações.' },
    { t: 'p', texto: 'Este trabalho apresenta a implementação básica do banco de dados de um sistema para concessionária de veículos, produto escolhido pelo grupo para desenvolvimento. O foco está na camada de dados: não faz parte do escopo o desenvolvimento de telas (*front-end*), e sim a definição do SGBD, a modelagem dos dados, a criação do banco e de suas tabelas e a carga e manipulação dos dados por meio da linguagem SQL.' },
    { t: 'p', texto: 'O documento está organizado da seguinte forma: a seção 2 apresenta os objetivos; a seção 3 justifica a escolha do SGBD; a seção 4 descreve a modelagem de dados, com o MER, o DER e o dicionário de dados; a seção 5 detalha a implementação, com todos os comandos utilizados e os resultados obtidos; e a seção 6 traz as conclusões. O script SQL completo está no Apêndice A. A formatação segue a NBR 14724 (ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS, 2011) e as referências, a NBR 6023 (ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS, 2018).' },

    // ── 2 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Objetivos' },
    { t: 'h2', texto: 'Objetivo geral' },
    { t: 'p', texto: 'Implementar um banco de dados relacional para um sistema de gestão de concessionária de veículos, contemplando a definição do SGBD, a criação do banco de dados, a criação da estrutura de tabelas e a carga de dados com os comandos INSERT, UPDATE e DELETE.' },
    { t: 'h2', texto: 'Objetivos específicos' },
    { t: 'alineas', itens: [
      'definir e justificar o SGBD utilizado;',
      'levantar as regras de negócio e as entidades do sistema;',
      'elaborar o Modelo Entidade-Relacionamento (MER) e o Diagrama Entidade-Relacionamento (DER);',
      'elaborar o dicionário de dados de todas as tabelas;',
      'criar o banco de dados e as tabelas, com chaves primárias, chaves estrangeiras e restrições de integridade;',
      'inserir, atualizar e excluir dados, registrando todos os comandos utilizados;',
      'verificar, por meio de consultas e testes, que os dados permanecem íntegros após as operações.',
    ] },

    // ── 3 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Escolha do banco de dados' },
    { t: 'p', texto: 'O SGBD escolhido foi o **MySQL**, na versão 8.0 *Community Edition*, distribuída gratuitamente pela Oracle Corporation sob a licença GPL (ORACLE CORPORATION, 2026). O MySQL é um SGBD relacional que utiliza a linguagem SQL e armazena os dados, por padrão, com o motor InnoDB. A escolha considerou os seguintes critérios:' },
    { t: 'alineas', itens: [
      'custo e licença: a edição *Community* é gratuita e de código aberto, sem as limitações de recursos típicas das edições gratuitas de SGBDs comerciais;',
      'integridade dos dados: o motor InnoDB oferece transações com as propriedades ACID e chaves estrangeiras com ações referenciais (RESTRICT, CASCADE e SET NULL), e, desde a versão 8.0.16, as restrições CHECK são efetivamente verificadas;',
      'adoção no mercado: é um dos SGBDs mais utilizados no mundo, com ampla documentação e comunidade, e está disponível na maioria dos serviços de hospedagem de sistemas *web*;',
      'ferramentas: o MySQL Workbench permite modelar o banco, executar os scripts e visualizar os resultados em ambiente gráfico;',
      'portabilidade: a sintaxe utilizada segue o padrão SQL, de modo que o script pode ser adaptado a outros SGBDs, como PostgreSQL ou MariaDB, com poucos ajustes.',
    ] },
    { t: 'p', texto: 'O {Q:sgbds} compara o MySQL com outros dois SGBDs considerados pelo grupo.' },
    { t: 'quadro', id: 'sgbds', titulo: 'Comparação entre os SGBDs considerados',
      cabecalho: ['Critério', 'MySQL 8.0', 'PostgreSQL', 'SQL Server Express'],
      larguras: [3.4, 3.2, 3.2, 3.2],
      linhas: [
        ['Licença', 'Código aberto (GPL)', 'Código aberto (PostgreSQL License)', 'Proprietária'],
        ['Custo', 'Gratuito', 'Gratuito', 'Gratuito, com limites de recursos'],
        ['Transações e chaves estrangeiras', 'Sim (motor InnoDB)', 'Sim', 'Sim'],
        ['Restrições CHECK', 'Sim (desde a 8.0.16)', 'Sim', 'Sim'],
        ['Ferramenta gráfica mais usada', 'MySQL Workbench', 'pgAdmin', 'SQL Server Management Studio'],
        ['Sistemas operacionais', 'Windows, Linux e macOS', 'Windows, Linux e macOS', 'Windows e Linux'],
      ],
      fonteTexto: 'Fonte: Elaborado pelos autores com base na documentação oficial de cada SGBD (2026).' },
    { t: 'p', texto: 'Os três atenderiam ao escopo do trabalho. O MySQL foi escolhido por reunir gratuidade sem limites de uso, recursos de integridade suficientes para as regras de negócio da concessionária e ampla disponibilidade em serviços de hospedagem, o que facilita uma evolução futura do projeto para um sistema *web*. Os comandos deste trabalho foram executados e validados no MySQL ' + versao + ', com o conjunto de caracteres utf8mb4, que representa corretamente os acentos da língua portuguesa.' },

    // ── 4 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Modelagem de dados' },
    { t: 'p', texto: 'A modelagem de dados foi feita em etapas, como recomenda Heuser (2009): primeiro o levantamento das regras de negócio; depois o modelo conceitual, independente de SGBD, que descreve os dados do ponto de vista do negócio; e por fim o modelo lógico, que já define as tabelas, colunas e chaves a serem implementadas.' },
    { t: 'h2', texto: 'Descrição do sistema e regras de negócio' },
    { t: 'p', texto: 'O sistema controla o funcionamento básico de uma concessionária: o cadastro de fornecedores, veículos, clientes e funcionários e o registro das vendas, que relacionam o cliente comprador, o funcionário responsável e o veículo vendido. As regras de negócio levantadas estão no {Q:regras} e orientaram todas as decisões de modelagem.' },
    { t: 'quadro', id: 'regras', titulo: 'Regras de negócio do sistema',
      cabecalho: ['Código', 'Regra'],
      larguras: [1.6, 14.4],
      linhas: [
        ['RN01', 'Cada fornecedor é identificado pelo CNPJ, que não pode se repetir.'],
        ['RN02', 'Um fornecedor pode fornecer vários veículos, e cada veículo vem de, no máximo, um fornecedor. Se o fornecedor for excluído, o veículo continua no estoque, sem fornecedor associado.'],
        ['RN03', 'Cada veículo tem marca, modelo, ano, cor, preço e situação. A placa, quando existir, é única; veículos 0 km ainda não emplacados ficam sem placa.'],
        ['RN04', 'A situação do veículo é Disponivel, Reservado ou Vendido, e todo veículo cadastrado começa como Disponivel.'],
        ['RN05', 'Cada cliente é identificado pelo CPF, que não pode se repetir.'],
        ['RN06', 'Uma venda envolve exatamente um cliente, um funcionário e um veículo, e registra a data e o valor negociado. Um veículo pode ser vendido no máximo uma vez e, ao ser vendido, passa à situação Vendido.'],
        ['RN07', 'Clientes, funcionários e veículos que constam em alguma venda não podem ser excluídos, para preservar o histórico de vendas.'],
        ['RN08', 'Preços, salários e valores de venda devem ser maiores que zero.'],
      ] },

    { t: 'h2', texto: 'Modelo Entidade-Relacionamento (MER)' },
    { t: 'p', texto: 'O Modelo Entidade-Relacionamento, proposto por Chen (1976), descreve os dados de forma conceitual por meio de entidades (objetos do mundo real sobre os quais se deseja guardar informações), atributos (propriedades das entidades) e relacionamentos (associações entre entidades). O MER deste trabalho foi representado na notação de Chen, com as cardinalidades no formato (mínima, máxima) usado por Heuser (2009): o par escrito junto a uma entidade indica com quantas ocorrências dela uma ocorrência da outra entidade se associa. Os atributos identificadores aparecem sublinhados.' },
    { t: 'p', texto: 'A {F:mer} apresenta o MER do sistema, com cinco entidades e quatro relacionamentos. Por conter muitos atributos, o diagrama foi colocado em uma página na orientação paisagem.' },
    { t: 'figura', id: 'mer', paisagem: true, titulo: 'Modelo Entidade-Relacionamento (MER) do sistema', arquivo: 'mer.png', largura: 22.5 },
    { t: 'p', texto: 'O {Q:relacionamentos} explica como ler cada relacionamento do MER.' },
    { t: 'quadro', id: 'relacionamentos', titulo: 'Relacionamentos do MER e suas cardinalidades',
      cabecalho: ['Relacionamento', 'Entidades', 'Tipo', 'Leitura'],
      larguras: [2.6, 3.6, 1.1, 8.7],
      linhas: [
        ['fornece', 'FORNECEDOR e VEÍCULO', '1:N', 'Um fornecedor fornece zero ou muitos veículos; um veículo vem de zero ou um fornecedor.'],
        ['é vendido em', 'VEÍCULO e VENDA', '1:1', 'Um veículo é vendido em zero ou uma venda; cada venda se refere a exatamente um veículo.'],
        ['realiza', 'CLIENTE e VENDA', '1:N', 'Um cliente realiza zero ou muitas compras; cada venda é feita para exatamente um cliente.'],
        ['registra', 'FUNCIONÁRIO e VENDA', '1:N', 'Um funcionário registra zero ou muitas vendas; cada venda é registrada por exatamente um funcionário.'],
      ] },
    { t: 'p', texto: 'A venda foi modelada como entidade, e não como um relacionamento entre cliente, funcionário e veículo, porque possui identidade própria (o número da venda) e atributos próprios (data e valor negociado), além de se associar a três entidades ao mesmo tempo.' },

    { t: 'h2', texto: 'Diagrama Entidade-Relacionamento (DER)' },
    { t: 'p', texto: 'O DER apresenta o modelo lógico do banco, obtido pela transformação do MER em tabelas (HEUSER, 2009). Foi usada a notação conhecida como pé de galinha (*crow\'s foot*), a mesma do MySQL Workbench, em que cada tabela aparece com suas colunas, tipos de dados e chaves, e as linhas entre as tabelas indicam as chaves estrangeiras e suas cardinalidades ({F:der}).' },
    { t: 'figura', id: 'der', paisagem: true, titulo: 'Diagrama Entidade-Relacionamento (DER) do banco concessionaria_db', arquivo: 'der.png', largura: 23 },
    { t: 'p', texto: 'Na transformação do modelo conceitual para o lógico, foram aplicadas as seguintes regras:' },
    { t: 'alineas', itens: [
      'cada entidade virou uma tabela, com nome no plural e sem acentos (`fornecedores`, `veiculos`, `clientes`, `funcionarios` e `vendas`), e cada atributo virou uma coluna;',
      'o identificador de cada entidade virou uma chave primária numérica gerada automaticamente pelo SGBD (AUTO_INCREMENT);',
      'nos relacionamentos 1:N, a chave primária do lado 1 foi copiada como chave estrangeira para a tabela do lado N: `fornecedor_id` em `veiculos`, e `cliente_id` e `funcionario_id` em `vendas`;',
      'no relacionamento 1:1 entre veículo e venda, a chave estrangeira `veiculo_id` ficou na tabela `vendas`, com a restrição UNIQUE, que impede que o mesmo veículo apareça em duas vendas;',
      'os atributos que identificam o registro no mundo real (CNPJ, CPF e placa) receberam a restrição UNIQUE.',
    ] },
    { t: 'p', texto: 'O {Q:chaves} resume as chaves de cada tabela e as ações referenciais escolhidas para as chaves estrangeiras.' },
    { t: 'quadro', id: 'chaves', titulo: 'Chaves primárias, chaves estrangeiras e ações referenciais',
      cabecalho: ['Tabela', 'Chave primária', 'Chave estrangeira', 'Referencia', 'Ao excluir', 'Ao atualizar'],
      larguras: [2.5, 2.2, 3.1, 3.2, 2.5, 2.5],
      linhas: [
        ['fornecedores', 'id', '–', '–', '–', '–'],
        ['veiculos', 'id', 'fornecedor_id', 'fornecedores (id)', 'SET NULL', 'CASCADE'],
        ['clientes', 'id', '–', '–', '–', '–'],
        ['funcionarios', 'id', '–', '–', '–', '–'],
        ['vendas', 'id', 'cliente_id', 'clientes (id)', 'RESTRICT', 'CASCADE'],
        ['vendas', 'id', 'funcionario_id', 'funcionarios (id)', 'RESTRICT', 'CASCADE'],
        ['vendas', 'id', 'veiculo_id', 'veiculos (id)', 'RESTRICT', 'CASCADE'],
      ] },
    { t: 'p', texto: 'Segundo Date (2004), a regra de integridade referencial determina que o banco não pode conter valores de chave estrangeira sem correspondência na chave primária referenciada. As ações referenciais definem como o SGBD mantém essa regra. A ação RESTRICT nas chaves estrangeiras de `vendas` garante a regra RN07: o SGBD recusa a exclusão de um cliente, funcionário ou veículo que já participou de uma venda. A ação SET NULL em `veiculos` implementa a regra RN02: se um fornecedor for excluído, seus veículos permanecem cadastrados, com a coluna `fornecedor_id` vazia. A ação CASCADE na atualização propaga automaticamente uma eventual mudança de chave primária para as tabelas que a referenciam.' },

    { t: 'h2', texto: 'Dicionário de dados' },
    { t: 'p', texto: 'O dicionário de dados descreve cada coluna das tabelas: o tipo de dado, se aceita valores nulos, as chaves e restrições a que está sujeita e o seu significado. Os Quadros 5 a 9 apresentam o dicionário das cinco tabelas do banco. Na coluna Chave, PK indica chave primária, FK chave estrangeira e UK valor único; na coluna Nulo, "Não" indica que o preenchimento é obrigatório (NOT NULL).' },
    dicionario('fornecedores', [
      ['id', 'INT', 'Não', 'PK', 'AUTO_INCREMENT', 'Código do fornecedor, gerado automaticamente'],
      ['nome', 'VARCHAR(100)', 'Não', '–', '–', 'Razão social ou nome fantasia'],
      ['cnpj', 'VARCHAR(18)', 'Não', 'UK', 'uq_fornecedor_cnpj', 'CNPJ no formato 00.000.000/0000-00'],
      ['telefone', 'VARCHAR(15)', 'Sim', '–', '–', 'Telefone de contato, com DDD'],
    ]),
    dicionario('veiculos', [
      ['id', 'INT', 'Não', 'PK', 'AUTO_INCREMENT', 'Código do veículo, gerado automaticamente'],
      ['marca', 'VARCHAR(50)', 'Não', '–', '–', 'Fabricante (ex.: Fiat, Toyota)'],
      ['modelo', 'VARCHAR(50)', 'Não', '–', '–', 'Modelo (ex.: Toro, Corolla)'],
      ['ano', 'YEAR', 'Não', '–', '–', 'Ano do modelo, com quatro dígitos'],
      ['cor', 'VARCHAR(30)', 'Sim', '–', '–', 'Cor predominante'],
      ['placa', 'VARCHAR(8)', 'Sim', 'UK', 'uq_veiculo_placa', 'Placa no padrão Mercosul; nula enquanto o veículo 0 km não é emplacado'],
      ['preco', 'DECIMAL(10,2)', 'Não', '–', 'CHECK (preco > 0)', 'Preço de venda anunciado, em reais'],
      ['status', 'VARCHAR(20)', 'Não', '–', "DEFAULT 'Disponivel'; CHECK: Disponivel, Reservado ou Vendido", 'Situação do veículo no estoque'],
      ['fornecedor_id', 'INT', 'Sim', 'FK', 'fornecedores (id), ON DELETE SET NULL', 'Fornecedor de quem o veículo foi adquirido'],
    ]),
    dicionario('clientes', [
      ['id', 'INT', 'Não', 'PK', 'AUTO_INCREMENT', 'Código do cliente, gerado automaticamente'],
      ['nome', 'VARCHAR(100)', 'Não', '–', '–', 'Nome completo'],
      ['cpf', 'VARCHAR(14)', 'Não', 'UK', 'uq_cliente_cpf', 'CPF no formato 000.000.000-00'],
      ['telefone', 'VARCHAR(15)', 'Sim', '–', '–', 'Telefone, com DDD'],
      ['email', 'VARCHAR(100)', 'Sim', '–', '–', 'Endereço de e-mail'],
      ['endereco', 'VARCHAR(150)', 'Sim', '–', '–', 'Logradouro, número, cidade e UF'],
    ]),
    dicionario('funcionarios', [
      ['id', 'INT', 'Não', 'PK', 'AUTO_INCREMENT', 'Código do funcionário, gerado automaticamente'],
      ['nome', 'VARCHAR(100)', 'Não', '–', '–', 'Nome completo'],
      ['cargo', 'VARCHAR(50)', 'Não', '–', '–', 'Cargo (ex.: Vendedor, Gerente de Vendas)'],
      ['salario', 'DECIMAL(10,2)', 'Não', '–', 'CHECK (salario > 0)', 'Salário mensal, em reais'],
      ['telefone', 'VARCHAR(15)', 'Sim', '–', '–', 'Telefone, com DDD'],
    ]),
    dicionario('vendas', [
      ['id', 'INT', 'Não', 'PK', 'AUTO_INCREMENT', 'Número da venda, gerado automaticamente'],
      ['cliente_id', 'INT', 'Não', 'FK', 'clientes (id), ON DELETE RESTRICT', 'Cliente que comprou o veículo'],
      ['funcionario_id', 'INT', 'Não', 'FK', 'funcionarios (id), ON DELETE RESTRICT', 'Funcionário responsável pela venda'],
      ['veiculo_id', 'INT', 'Não', 'FK, UK', 'veiculos (id), ON DELETE RESTRICT; uq_venda_veiculo', 'Veículo vendido; o UNIQUE impede vendê-lo duas vezes'],
      ['data_venda', 'DATE', 'Não', '–', '–', 'Data em que a venda foi fechada'],
      ['valor_venda', 'DECIMAL(10,2)', 'Não', '–', 'CHECK (valor_venda > 0)', 'Valor negociado, em reais, que pode diferir do preço anunciado'],
    ]),
    { t: 'p', texto: 'Os valores monetários usam o tipo DECIMAL(10,2), numérico exato que evita os erros de arredondamento dos tipos de ponto flutuante e comporta valores de até 99.999.999,99. CPF, CNPJ, telefone e placa foram armazenados como texto (VARCHAR) porque não são usados em cálculos e podem conter zeros à esquerda e caracteres de formatação.' },

    // ── 5 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Implementação' },
    { t: 'p', texto: 'A implementação seguiu as quatro etapas propostas para o trabalho: definição do SGBD (seção 3), criação do banco de dados, criação da estrutura de tabelas e carga de dados. Todos os comandos desta seção fazem parte de um único arquivo, `script_concessionaria.sql`, reproduzido no Apêndice A, que pode ser executado de uma só vez no MySQL Workbench ou pelo terminal, com o comando `mysql -u root -p < script_concessionaria.sql`.' },
    { t: 'p', texto: 'Os comandos SQL costumam ser agrupados em subconjuntos: a DDL, que define a estrutura do banco (CREATE, DROP); a DML, que manipula os dados (INSERT, UPDATE, DELETE); a DQL, que consulta os dados (SELECT); e a TCL, que controla as transações (START TRANSACTION, COMMIT). Todos eles aparecem nas etapas a seguir.' },

    { t: 'h2', texto: 'Criação do banco de dados' },
    { t: 'p', texto: 'O {C:banco} cria o banco de dados `concessionaria_db`. O comando SET NAMES informa ao servidor que o script está codificado em UTF-8. O comando DROP DATABASE IF EXISTS apaga uma versão anterior do banco, o que permite executar o script várias vezes, sempre a partir do zero. O conjunto de caracteres utf8mb4 armazena qualquer caractere Unicode, inclusive os acentos do português, e o *collation* utf8mb4_unicode_ci faz as comparações de texto ignorarem a diferença entre maiúsculas e minúsculas. Por fim, o comando USE seleciona o banco para os comandos seguintes.' },
    { t: 'codigo', id: 'banco', titulo: 'Criação do banco de dados', codigo: trecho('SET NAMES', 'USE concessionaria_db;') },

    { t: 'h2', texto: 'Criação da estrutura de tabelas' },
    { t: 'p', texto: 'As tabelas foram criadas com o comando CREATE TABLE, em uma ordem que respeita as dependências entre elas: primeiro `fornecedores`, depois `veiculos`, que a referencia; em seguida `clientes` e `funcionarios`; e por último `vendas`, que referencia três das anteriores. Uma chave estrangeira só pode ser criada quando a tabela referenciada já existe. Todas as tabelas usam o motor InnoDB, padrão do MySQL 8.0, que oferece suporte a chaves estrangeiras e a transações (ORACLE CORPORATION, 2026).' },
    { t: 'p', texto: 'As restrições foram declaradas com nome, pela cláusula CONSTRAINT, o que deixa as mensagens de erro do SGBD mais claras, como se verá na seção 5.4. As restrições utilizadas foram:' },
    { t: 'alineas', itens: [
      'PRIMARY KEY com AUTO_INCREMENT: identifica cada linha, com numeração gerada pelo SGBD;',
      'NOT NULL: torna obrigatório o preenchimento da coluna;',
      'UNIQUE: impede valores repetidos na coluna (CNPJ, CPF, placa e veículo da venda);',
      "DEFAULT: define o valor usado quando a coluna não é informada no INSERT (a situação 'Disponivel');",
      'CHECK: valida o conteúdo da coluna (valores maiores que zero e situação dentro da lista permitida);',
      'FOREIGN KEY: liga a tabela a outra e define o que acontece ao excluir ou atualizar a linha referenciada.',
    ] },
    { t: 'p', texto: 'Os Códigos 2 a 6 apresentam a criação de cada tabela.' },
    { t: 'codigo', titulo: 'Criação da tabela fornecedores', codigo: trecho('CREATE TABLE fornecedores', ') ENGINE = InnoDB;') },
    { t: 'codigo', titulo: 'Criação da tabela veiculos', codigo: trecho('CREATE TABLE veiculos', ') ENGINE = InnoDB;') },
    { t: 'codigo', titulo: 'Criação da tabela clientes', codigo: trecho('CREATE TABLE clientes', ') ENGINE = InnoDB;') },
    { t: 'codigo', titulo: 'Criação da tabela funcionarios', codigo: trecho('CREATE TABLE funcionarios', ') ENGINE = InnoDB;') },
    { t: 'codigo', id: 'tab_vendas', titulo: 'Criação da tabela vendas', codigo: trecho('CREATE TABLE vendas', ') ENGINE = InnoDB;') },
    { t: 'p', texto: 'Para conferir a estrutura criada, o catálogo do próprio SGBD (o banco `information_schema`) foi consultado com o {C:cod_restricoes}. O resultado, no {Q:restricoes}, mostra as 17 restrições criadas nas cinco tabelas: 5 chaves primárias, 4 restrições UNIQUE, 4 restrições CHECK e 4 chaves estrangeiras.' },
    { t: 'codigo', id: 'cod_restricoes', titulo: 'Consulta às restrições criadas no banco', codigo: [
      'SELECT TABLE_NAME AS tabela, CONSTRAINT_NAME AS restricao,',
      '       CONSTRAINT_TYPE AS tipo',
      'FROM information_schema.TABLE_CONSTRAINTS',
      "WHERE TABLE_SCHEMA = 'concessionaria_db'",
      'ORDER BY TABLE_NAME, CONSTRAINT_TYPE, CONSTRAINT_NAME;',
    ].join('\n') },
    { t: 'quadro', id: 'restricoes', titulo: 'Restrições criadas no banco concessionaria_db',
      ...r('restricoes'), larguras: [4, 6, 4], mono: [0, 1, 2], fonteTexto: 'execucao' },

    { t: 'h2', texto: 'Carga de dados' },
    { t: 'p', texto: 'Com a estrutura pronta, a carga de dados foi feita com os três comandos da DML pedidos no trabalho: INSERT, para incluir linhas; UPDATE, para alterar linhas existentes; e DELETE, para removê-las. Todos os dados utilizados são fictícios.' },
    { t: 'h3', texto: 'Inserção de dados (INSERT)' },
    { t: 'p', texto: 'O {C:insert} insere os cadastros iniciais. Cada comando INSERT inclui várias linhas de uma vez: primeiro lista as colunas e, em seguida, os valores de cada linha, na mesma ordem. A coluna `id` não é informada, pois é gerada pelo AUTO_INCREMENT. Na tabela `veiculos`, a coluna `status` também foi omitida e recebeu o valor padrão \'Disponivel\', e o Renault Kwid, por ser 0 km e ainda não emplacado, foi inserido com a placa NULL.' },
    { t: 'codigo', id: 'insert', titulo: 'Inserção dos cadastros iniciais', codigo: trecho('INSERT INTO fornecedores', "'(67) 99555-3333');") },
    { t: 'p', texto: 'Após as inserções, o banco passou a ter 3 fornecedores, 7 veículos, 4 clientes e 3 funcionários. O {Q:veiculos_insert} mostra o conteúdo da tabela `veiculos` nesse momento, com os códigos gerados pelo AUTO_INCREMENT, a situação preenchida pelo valor padrão e a placa nula do veículo 0 km.' },
    { t: 'quadro', id: 'veiculos_insert', titulo: 'Tabela veiculos após a inserção',
      ...r('apos_insert_veiculos'), larguras: [0.7, 2.1, 1.7, 1.1, 1.7, 1.8, 2.0, 2.0, 2.4],
      fonte: 18, alinharNumeros: true, fonteTexto: 'execucao' },

    { t: 'h3', texto: 'Registro das vendas (INSERT e UPDATE em transação)' },
    { t: 'p', texto: 'Registrar uma venda exige duas operações: incluir a linha na tabela `vendas` e mudar a situação do veículo para \'Vendido\'. Se apenas a primeira fosse gravada, por uma falha no meio do caminho, o veículo continuaria aparecendo como disponível mesmo já tendo sido vendido. Por isso, as duas operações foram agrupadas em uma transação, delimitada por START TRANSACTION e COMMIT. Pela propriedade de atomicidade, ou todas as operações de uma transação são efetivadas no banco, ou nenhuma é (SILBERSCHATZ; KORTH; SUDARSHAN, 2012). O {C:vendas} registra as três vendas.' },
    { t: 'codigo', id: 'vendas', titulo: 'Registro das vendas em transações', codigo: trecho('-- Cada venda grava', 'COMMIT;', { ultimo: true }) },
    { t: 'p', texto: 'O {Q:vendas_tab} mostra a tabela `vendas` após o registro. Os veículos 1, 4 e 5 passaram à situação \'Vendido\'.' },
    { t: 'quadro', id: 'vendas_tab', titulo: 'Tabela vendas após o registro das vendas',
      ...r('apos_vendas'), larguras: [1, 2.4, 2.8, 2.4, 3, 3], alinharNumeros: true, fonteTexto: 'execucao' },

    { t: 'h3', texto: 'Atualização de dados (UPDATE)' },
    { t: 'p', texto: 'O comando UPDATE altera colunas de linhas já existentes. A cláusula WHERE define quais linhas são afetadas; sem ela, todas as linhas da tabela seriam alteradas. O {C:update} traz quatro atualizações: o reajuste de preço de um veículo, a reserva de outro, a troca de telefone de uma cliente e um reajuste de 5% no salário de todos os vendedores, este último calculado a partir do valor atual da própria coluna.' },
    { t: 'codigo', id: 'update', titulo: 'Atualizações de dados', codigo: trecho('-- Reajuste de preço', "WHERE cargo = 'Vendedor';") },
    { t: 'p', texto: 'O {Q:antes_depois} compara os valores antes e depois das atualizações. O último comando afetou duas linhas, uma para cada vendedor.' },
    { t: 'quadro', id: 'antes_depois', titulo: 'Valores antes e depois das atualizações',
      cabecalho: ['Atualização', 'Linhas afetadas', 'Antes', 'Depois'],
      larguras: [5.2, 2.2, 4.3, 4.3],
      alinharNumeros: true,
      linhas: (() => {
        const a = resultados.antes_update.linhas;
        const d = resultados.depois_update.linhas;
        return [
          ['Preço do Chevrolet Onix', '1', `preco = ${a[0][1]}`, `preco = ${d[0][1]}`],
          ['Situação do Jeep Compass', '1', `status = ${a[1][1]}`, `status = ${d[1][1]}`],
          ['Telefone de Mariana Souza', '1', a[2][1], d[2][1]],
          [`Salário dos vendedores (${a[3][0]} e ${a[4][0]})`, '2', `salario = ${a[3][1]}`, `salario = ${d[3][1]}`],
        ];
      })(),
      fonteTexto: 'execucao' },

    { t: 'h3', texto: 'Exclusão de dados (DELETE)' },
    { t: 'p', texto: 'O comando DELETE remove linhas de uma tabela, também filtradas pela cláusula WHERE. O {C:delete} exclui o Chevrolet Onix, devolvido ao fornecedor antes de ser vendido, e o cliente Ricardo Alves, que nunca realizou compras. As duas exclusões foram aceitas porque nenhuma venda faz referência a essas linhas.' },
    { t: 'codigo', id: 'delete', titulo: 'Exclusões de dados', codigo: trecho('-- Remove um veículo', "WHERE cpf = '987.654.321-00';") },

    { t: 'h2', texto: 'Testes de integridade' },
    { t: 'p', texto: 'Para confirmar que as restrições criadas protegem os dados, foram executados três comandos que violam regras de negócio ({C:cod_testes}). No script, esses comandos ficam comentados, para não interromper a execução.' },
    { t: 'codigo', id: 'cod_testes', titulo: 'Comandos que violam as regras de negócio',
      codigo: trecho('-- a) Excluir', "-- UPDATE veiculos SET status = 'Vendida' WHERE id = 6;")
        .split('\n').map((l) => (/^-- (DELETE|INSERT|UPDATE|VALUES| {4}\()/.test(l) ? l.slice(3) : l)).join('\n') },
    { t: 'p', texto: 'Os três comandos foram recusados pelo SGBD, que devolveu as mensagens de erro reproduzidas no {Q:testes}.' },
    { t: 'quadro', id: 'testes', titulo: 'Resultado dos testes de integridade',
      cabecalho: ['Teste', 'Regra', 'Resposta do MySQL'],
      larguras: [4.2, 1.4, 10.4],
      mono: [2],
      linhas: [
        ['a) Excluir a cliente Mariana Souza, que tem uma venda', 'RN07', resultados.teste_fk],
        ['b) Vender novamente o Volkswagen Gol', 'RN06', resultados.teste_unique],
        ["c) Gravar a situação 'Vendida', que não existe", 'RN04', resultados.teste_check],
      ],
      fonteTexto: 'execucao' },
    { t: 'p', texto: 'No teste a, a chave estrangeira `fk_venda_cliente`, com a ação RESTRICT, impediu a exclusão de um cliente que consta em uma venda. No teste b, a restrição `uq_venda_veiculo` impediu que o mesmo veículo fosse vendido duas vezes. No teste c, a restrição `ck_veiculo_status` recusou um valor fora da lista permitida. Nos três casos o banco permaneceu inalterado, o que demonstra que a integridade dos dados é garantida pelo próprio SGBD, independentemente da aplicação que venha a utilizá-lo.' },

    { t: 'h2', texto: 'Consultas de verificação' },
    { t: 'p', texto: 'Por fim, o comando SELECT foi usado para conferir o resultado da carga. As consultas do {C:consultas} contam os registros de cada tabela, listam os veículos em estoque com o nome do fornecedor, reúnem os dados de cada venda a partir de quatro tabelas, por meio de junções (JOIN) pelas chaves estrangeiras, e somam o valor vendido por funcionário.' },
    { t: 'codigo', id: 'consultas', titulo: 'Consultas de verificação', codigo: trecho('-- Quantidade de registros', 'ORDER BY total_vendido DESC;') },
    { t: 'p', texto: 'Os resultados estão nos Quadros 15 a 18. Ao final da carga, o banco ficou com 3 fornecedores, 6 veículos, 3 clientes, 3 funcionários e 3 vendas ({Q:contagem}).' },
    { t: 'quadro', id: 'contagem', titulo: 'Quantidade de registros por tabela ao final da carga',
      ...r('final_contagem'), larguras: [5, 3], alinharNumeros: true, fonteTexto: 'execucao' },
    { t: 'p', texto: 'A segunda consulta usa LEFT JOIN, e não JOIN, para que um veículo sem fornecedor (situação prevista na regra RN02) também apareça na lista de estoque ({Q:estoque}).' },
    { t: 'quadro', id: 'estoque', titulo: 'Veículos em estoque, com o fornecedor',
      ...r('final_estoque'), larguras: [2, 2, 1.2, 2.2, 2.2, 5.4], alinharNumeros: true, fonteTexto: 'execucao' },
    { t: 'p', texto: 'A terceira consulta junta quatro tabelas para apresentar cada venda com os nomes do cliente e do funcionário e a identificação do veículo ({Q:vendas_final}).' },
    { t: 'quadro', id: 'vendas_final', titulo: 'Vendas realizadas',
      ...r('final_vendas'), larguras: [0.8, 3.6, 2.6, 3.2, 2.6, 2.6], alinharNumeros: true, fonteTexto: 'execucao' },
    { t: 'p', texto: 'A última consulta agrupa as vendas por funcionário (GROUP BY) e usa as funções COUNT e SUM. Com LEFT JOIN, a gerente, que não registrou vendas, também aparece, com total zero ({Q:por_funcionario}).' },
    { t: 'quadro', id: 'por_funcionario', titulo: 'Total vendido por funcionário',
      ...r('final_por_funcionario'), larguras: [4.5, 4.5, 2, 3], alinharNumeros: true, fonteTexto: 'execucao' },

    { t: 'h2', texto: 'Resumo dos comandos utilizados' },
    { t: 'p', texto: 'O {Q:resumo_comandos} resume os comandos utilizados em cada etapa da implementação.' },
    { t: 'quadro', id: 'resumo_comandos', titulo: 'Comandos SQL utilizados na implementação',
      cabecalho: ['Etapa', 'Comandos', 'Subconjunto'],
      larguras: [4.2, 8.8, 3],
      linhas: [
        ['Criação do banco', 'SET NAMES, DROP DATABASE IF EXISTS, CREATE DATABASE, USE', 'DDL'],
        ['Estrutura de tabelas', 'CREATE TABLE com PRIMARY KEY, AUTO_INCREMENT, NOT NULL, UNIQUE, DEFAULT, CHECK e FOREIGN KEY', 'DDL'],
        ['Inserção de dados', 'INSERT INTO ... VALUES', 'DML'],
        ['Registro das vendas', 'START TRANSACTION, INSERT, UPDATE, COMMIT', 'TCL e DML'],
        ['Atualização de dados', 'UPDATE ... SET ... WHERE', 'DML'],
        ['Exclusão de dados', 'DELETE FROM ... WHERE', 'DML'],
        ['Verificação', 'SELECT com JOIN, LEFT JOIN, GROUP BY, COUNT, SUM e consulta ao information_schema', 'DQL'],
      ] },

    // ── 6 ────────────────────────────────────────────────────────────
    { t: 'h1', texto: 'Conclusão' },
    { t: 'p', texto: 'O trabalho cumpriu as quatro etapas propostas: o SGBD MySQL 8.0 foi definido e justificado, o banco `concessionaria_db` foi criado, a estrutura de cinco tabelas foi implementada com chaves e restrições de integridade e a carga de dados foi realizada com os comandos INSERT, UPDATE e DELETE, todos documentados e executados com sucesso.' },
    { t: 'p', texto: 'A modelagem em dois níveis mostrou-se importante para a implementação. O MER permitiu discutir as regras do negócio sem se preocupar com detalhes técnicos, e o DER, junto com o dicionário de dados, serviu de roteiro direto para os comandos CREATE TABLE. Decisões tomadas na modelagem, como a restrição UNIQUE na chave estrangeira `veiculo_id` e a ação RESTRICT nas exclusões, foram confirmadas nos testes de integridade: o próprio SGBD recusou a venda repetida de um veículo e a exclusão de um cliente com histórico de compras.' },
    { t: 'p', texto: 'Também ficou evidente o valor das transações: ao agrupar o registro da venda e a atualização da situação do veículo, o banco nunca fica em um estado intermediário, em que um veículo vendido aparece como disponível.' },
    { t: 'p', texto: 'Como trabalhos futuros, o modelo pode ser ampliado com tabelas de formas de pagamento e financiamento, agendamento de *test drive*, histórico de manutenção e comissões dos vendedores, além de gatilhos (*triggers*) que atualizem automaticamente a situação do veículo e visões (*views*) para relatórios gerenciais. O banco também está pronto para ser utilizado por uma aplicação com interface gráfica, que poderá ser desenvolvida em uma etapa posterior.' },

    // ── Pós-textuais ─────────────────────────────────────────────────
    { t: 'referencias', itens: [
      'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 6023**: informação e documentação: referências: elaboração. Rio de Janeiro: ABNT, 2018.',
      'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **NBR 14724**: informação e documentação: trabalhos acadêmicos: apresentação. Rio de Janeiro: ABNT, 2011.',
      'CHEN, Peter Pin-Shan. The entity-relationship model: toward a unified view of data. **ACM Transactions on Database Systems**, New York, v. 1, n. 1, p. 9-36, mar. 1976.',
      'DATE, C. J. **Introdução a sistemas de bancos de dados**. Rio de Janeiro: Elsevier, 2004.',
      'ELMASRI, Ramez; NAVATHE, Shamkant B. **Sistemas de banco de dados**. 7. ed. São Paulo: Pearson Education do Brasil, 2018.',
      'HEUSER, Carlos Alberto. **Projeto de banco de dados**. 6. ed. Porto Alegre: Bookman, 2009.',
      'ORACLE CORPORATION. **MySQL 8.0 reference manual**. [*S. l.*]: Oracle, 2026. Disponível em: https://dev.mysql.com/doc/refman/8.0/en/. Acesso em: 22 set. 2026.',
      'SILBERSCHATZ, Abraham; KORTH, Henry F.; SUDARSHAN, S. **Sistema de banco de dados**. 6. ed. Rio de Janeiro: Elsevier, 2012.',
    ] },
    { t: 'apendice', titulo: 'APÊNDICE A – SCRIPT SQL COMPLETO',
      texto: 'Script `script_concessionaria.sql`, entregue junto com este documento. Executado de uma só vez, ele recria o banco do zero, com a estrutura e todos os dados descritos na seção 5.',
      codigo: require('fs').readFileSync(require('path').join(__dirname, '..', 'script_concessionaria.sql'), 'utf8').trim() },
  ];

  return { capa, resumo, siglas, blocos };
};
