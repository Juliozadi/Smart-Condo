/* Seções 12 a 18. */

// ── 12 Acessibilidade ───────────────────────────────────────────────
const acessibilidade = {
  intro: 'Utilização de recursos para promover a inclusão de pessoas com deficiência ou dificuldade em utilizar serviços, nesse caso, digitais. Nós utilizaremos ferramentas web de alteração de tamanho de texto, cores e visualizações para garantir a acessibilidade de usuários com deficiências comunicacionais e digitais.',
  itens: [
    { n: '12.1', nome: 'Boas práticas', paragrafos: [
      'Criação de telas e visuais intuitivos e acessíveis, com cores não extravagantes e de pouca saturação, pensando em pessoas com daltonismo e/ou deficiências visuais, toda a paleta de cores do SmartCondo foi calculada usando padrões de estilo já utilizados nos meios digitais e que garantem o conforto visual ao usuário.',
      'Além da paleta, foram adotadas práticas que atendem às recomendações da WCAG (Web Content Accessibility Guidelines). Todos os campos de formulário têm rótulo associado, de modo que um leitor de tela anuncie corretamente o que está sendo pedido. Os elementos clicáveis respeitam a área mínima de toque de 24 por 24 pixels, recomendada para quem usa o sistema pelo celular. As telas também foram verificadas em largura de 360 pixels, para garantir que nenhum conteúdo fique cortado ou exija rolagem lateral.',
      'O contraste entre texto e fundo é tratado por um conjunto de cores semânticas — sucesso, aviso, erro, informação e a cor da marca aplicada a texto — com um valor próprio para o tema claro e outro para o escuro. Cada valor foi escolhido por busca, aumentando ou diminuindo a luminosidade até alcançar a razão mínima de 4,5:1 exigida pela WCAG nível AA, e essa verificação foi feita contra todos os fundos em que a cor de fato aparece: as superfícies do tema, as tintas translúcidas dos selos de situação e as pílulas de identificação. No modo de alto contraste, os mesmos elementos assumem valores que alcançam 7:1, a razão do nível AAA.',
      'A conferência não é visual: um script percorre as telas do sistema nos dois temas e em duas larguras de tela, mede a razão de contraste de cada texto visível e acusa o que ficar abaixo do mínimo. A primeira execução encontrou 305 textos em desacordo, sendo o pior deles um título com razão de 1,21 — praticamente ilegível. Depois da correção, a mesma medição não encontra nenhum.',
    ]},
    { n: '12.2', nome: 'VLibras', paragrafos: [
      'O VLibras é um conjunto de ferramentas gratuitas e de código aberto que traduz conteúdos digitais (texto, áudio e vídeo) em português para Libras, tornando computadores, celulares e plataformas Web mais acessíveis para as pessoas surdas. Será utilizado no projeto SmartCondo com o intuito de atender às necessidades dos usuários com deficiências auditivas.',
    ]},
    { n: '12.3', nome: 'Tamanho da fonte', paragrafos: [
      'O usuário terá a opção de manipular o tamanho da fonte de todo o texto acessível da aplicação, de acordo com a necessidade preferível, a fim de promover a acessibilidade visual do usuário do SmartCondo.',
    ]},
    { n: '12.4', nome: 'Mudança de cores', paragrafos: [
      'O usuário também poderá aplicar recursos para mudança das cores da aplicação, como o modo escuro ou claro, de acordo com a preferência dele. Por padrão, o SmartCondo usará a definição de modo de cor do sistema operacional do usuário, que por sua vez, pode alterar a qualquer momento.',
    ]},
  ],
};

// ── 13 Arquitetura e banco de dados (nova) ──────────────────────────
const arquitetura = {
  paragrafos: [
    'O SmartCondo está dividido em três camadas independentes, que se comunicam entre si mas podem ser desenvolvidas e testadas separadamente.',
    'A primeira é o front-end, escrito em HTML, CSS e JavaScript puro, sem frameworks. É o que o usuário enxerga no navegador. Toda a conversa com o servidor passa por um único arquivo, o api.js, que centraliza o endereço da API, o token da sessão e o tratamento dos erros. Com isso, nenhuma tela precisa saber como uma requisição é montada, e uma mudança no formato de autenticação é feita em um lugar só.',
    'A segunda é a API REST, escrita em Python com FastAPI. É ela que aplica as regras do negócio: quem pode cadastrar quem, se uma reserva conflita com outra já existente, se um porteiro tem permissão para registrar uma ocorrência. Nenhuma dessas decisões fica no navegador, porque o código do navegador pode ser alterado pelo usuário.',
    'A terceira é o banco de dados PostgreSQL, acessado pela API por meio do SQLAlchemy. As mudanças de estrutura são versionadas com o Alembic.',
    'Fora dessas três camadas, o sistema depende de um serviço de envio de mensagens. Os códigos de confirmação de cadastro e de recuperação de senha saem por correio eletrônico, usando um servidor SMTP configurado por variáveis de ambiente, e a mensagem vai em duas versões, uma em texto simples e outra formatada. Sem essa configuração o código não é entregue a ninguém, o que travaria o cadastro do morador; por isso a aplicação avisa ao iniciar quando está em modo de produção sem o servidor de correio definido.',
    'Os mesmos códigos podem ir por SMS, por meio do provedor Twilio, quando as credenciais dele estão configuradas. A tela consulta a API para saber se o SMS está disponível e só oferece a opção nesse caso; sem provedor, a API recusa o pedido e orienta a usar o e-mail, em vez de gerar um código que nunca chegaria. O texto é curto de propósito, porque uma mensagem acima de 160 caracteres é cobrada como duas.',
    'As fotos de perfil ficam gravadas em uma pasta do servidor, fora do banco, com um nome aleatório gerado no envio; o banco guarda apenas o caminho. As fotos tiradas na portaria, as anexadas às ocorrências, os documentos enviados no cadastro do morador e os documentos do condomínio publicados pelo síndico também ficam em pastas do servidor, mas separadas e sem endereço público: por serem dados pessoais de terceiros, só saem por rotas da API que conferem o token e quem tem direito a ver cada arquivo. O chat entre síndico, porteiros e moradores usa a mesma API: enquanto a conversa está aberta, a tela consulta as mensagens novas a cada quatro segundos, o que atende ao volume de um condomínio sem exigir uma conexão permanente com o servidor.',
  ],
  subsecoes: [
    { n: '13.1', nome: 'Modelagem do banco de dados', paragrafos: [
      'O banco tem 19 tabelas, ligadas por 39 chaves estrangeiras. A tabela central é usuarios, que guarda os quatro papéis do sistema em um único lugar, diferenciados por uma coluna de papel. Essa escolha evita quatro tabelas quase idênticas e permite que o login, a recuperação de senha e o perfil funcionem igual para todos.',
      'Há um ponto de atenção na modelagem: condominios aponta para o síndico responsável e usuarios aponta para o condomínio, o que forma uma referência circular. Por isso, nos scripts de criação, todas as tabelas são criadas primeiro e as chaves estrangeiras só depois.',
    ], tabela: [
      ['Tabela', 'O que guarda'],
      ['condominios', 'Condomínios cadastrados pelo administrador'],
      ['unidades', 'Apartamentos ou casas de cada condomínio'],
      ['usuarios', 'Administradores, síndicos, porteiros e moradores'],
      ['permissoes_porteiro', 'O que cada porteiro pode fazer, definido pelo síndico'],
      ['codigos_verificacao', 'Códigos de confirmação e de recuperação de senha'],
      ['espacos_comuns', 'Salão, churrasqueira, piscina, academia e demais áreas'],
      ['reservas', 'Pedidos de reserva, aprovados ou recusados pelo síndico'],
      ['registros_ocupacao', 'Contagem de pessoas nas áreas de uso livre'],
      ['preferencias_cobranca', 'Dia do vencimento e forma de pagamento do morador'],
      ['cobrancas', 'Taxa condominial por unidade e competência'],
      ['pagamentos', 'Pagamentos recebidos, com meio, valor e data'],
      ['comunicados', 'Avisos publicados pelo síndico'],
      ['leituras_comunicado', 'Quem já leu cada comunicado'],
      ['visitantes', 'Registro de visitantes, com a foto do vídeo porteiro'],
      ['encomendas', 'Encomendas recebidas na portaria, com a foto do volume'],
      ['ocorrencias', 'Chamados abertos por moradores, porteiros ou síndico'],
      ['movimentacoes_veiculo', 'Entradas e saídas do estacionamento'],
      ['ordens_servico', 'Manutenção aberta e acompanhada pelo síndico'],
      ['documentos', 'Atas, convenção, regimento e plantas'],
      ['documentos_cadastro', 'RG, comprovante de residência e escritura enviados no cadastro do morador'],
    ]},
    { n: '13.2', nome: 'Segurança dos dados', paragrafos: [
      'As senhas nunca são guardadas em texto puro: o sistema armazena apenas o hash gerado pelo algoritmo bcrypt, que é de mão única. Mesmo com acesso ao banco, não é possível recuperar a senha original.',
      'O acesso às rotas da API é controlado por token JWT, emitido no login e enviado em toda requisição seguinte. O token carrega o papel do usuário, e cada rota declara qual papel pode acessá-la. Um morador que tente acessar uma rota do síndico recebe erro de permissão, mesmo que altere o código da tela no próprio navegador.',
      'O sistema também evita revelar informação desnecessária. O erro de login é o mesmo para e-mail inexistente e senha errada, para não permitir descobrir quais e-mails estão cadastrados. Na tela de reservas, a mensagem de conflito informa o horário já ocupado, mas nunca quem reservou, atendendo ao sigilo pedido na seção 6.',
      'Para que a senha não possa ser descoberta por tentativa e erro, o login conta as tentativas malsucedidas e bloqueia a conta por quinze minutos depois de cinco senhas erradas seguidas. O bloqueio é temporário de propósito: fosse permanente, bastaria errar a senha de alguém repetidamente para deixá-lo fora do sistema. Acertar a senha zera a contagem. A verificação do bloqueio acontece antes da conferência da senha, de modo que uma conta bloqueada não consuma processamento a cada nova tentativa.',
      'Toda decisão tomada dentro do sistema guarda o registro de quem a tomou e quando. Isso vale para a aprovação de uma reserva, para a resposta a uma ocorrência e também para a aprovação do cadastro de um morador, que é a decisão que concede acesso ao sistema; quando o cadastro é recusado, o motivo fica gravado junto.',
      'O código de seis dígitos usado na confirmação do cadastro e na recuperação de senha também tem limite de tentativas, e por um motivo prático: sem ele, bastaria pedir a recuperação de um endereço conhecido e percorrer as combinações até acertar, o que daria acesso à conta alheia. O código é guardado embaralhado, vale por quinze minutos e é descartado assim que usado ou quando o limite se esgota. Ele nunca é registrado no diário do servidor, para que ter acesso a esse arquivo não signifique conseguir entrar nas contas.',
      'As respostas da API trazem cabeçalhos que fecham portas deixadas abertas pelo comportamento padrão do navegador: impedir que o tipo do conteúdo seja adivinhado, impedir que a API seja exibida dentro de um quadro de outra página e restringir a origem do que a resposta pode carregar. Publicado o sistema, é acrescentado também o cabeçalho que obriga o uso de conexão segura.',
      'As fotos de visitantes e de encomendas e os documentos do cadastro do morador são dados pessoais de terceiros e recebem tratamento próprio. O tipo de cada arquivo é conferido pelos primeiros bytes do conteúdo, e não pela extensão informada, que é escolhida por quem envia. Os arquivos não têm endereço público: a foto de um visitante só é entregue ao morador da unidade visitada, ao síndico e ao porteiro com permissão de registrar visitantes, e os documentos do cadastro só ao síndico do condomínio. Os documentos do condomínio seguem a mesma regra: o que vale para todos abre para quem é do condomínio, e o de uma unidade, como a planta, só para quem mora nela. A tela baixa o arquivo com o token e o exibe a partir da memória do navegador, sem que ele fique guardado em cache. As fotos da portaria são apagadas depois de noventa dias, e os documentos do cadastro são apagados quando o cadastro é recusado ou o morador é inativado, porque a finalidade que justificava guardá-los deixou de existir.',
      'Quem acabou de se cadastrar ainda não pode entrar no sistema, mas precisa enviar os documentos. Para isso, o cadastro devolve uma autorização de uso único em propósito: ela vale por uma hora, só permite enviar os documentos e a foto daquele cadastro, deixa de valer quando o síndico decide e nunca abre uma sessão, nem depois da aprovação.',
      'O envio de códigos também tem limite: um por minuto e no máximo cinco por hora para cada pessoa. Sem ele, qualquer um poderia pedir a recuperação de senha com o e-mail de outra pessoa sem parar — e cada SMS é pago —, e cada código novo traria mais tentativas para adivinhar. Quando o limite barra um pedido, a resposta é a mesma de sempre, para não revelar quem está cadastrado, e a tela mostra quanto falta para poder reenviar. Os erros de senha na troca de senha contam para o mesmo bloqueio do login.',
      'As permissões do porteiro, definidas pelo síndico, são verificadas em toda gravação e também nas consultas: sem a permissão de registrar visitantes, por exemplo, o porteiro também não lista os visitantes. A tela também as consulta, para esconder o que aquele porteiro não pode fazer em vez de deixá-lo preencher um formulário que seria recusado no envio; a decisão, porém, continua sendo da API, e não do navegador.',
      'Por fim, o tratamento dos dados pessoais é descrito em dois documentos acessíveis pelo próprio sistema: os Termos de Uso e a Política de Privacidade. A política relaciona, um a um, os dados que o sistema guarda, a base legal de cada tratamento, o prazo de guarda e os direitos previstos no artigo 18 da Lei 13.709/2018, a Lei Geral de Proteção de Dados. O aceite desses documentos é condição para concluir o cadastro.',
    ], tabela: null },
  ],
};

// ── 14 API REST (nova) ──────────────────────────────────────────────
const api = {
  paragrafos: [
    'A comunicação entre o front-end e o banco de dados acontece por uma API REST, com 99 endpoints distribuídos em treze módulos. Todos os endereços começam com /api/v1, o que permite publicar uma versão 2 no futuro sem quebrar as telas que já usam a versão atual.',
    'As mensagens de erro são padronizadas e vêm em português, para que a tela possa exibir ao usuário exatamente o que o servidor respondeu, sem precisar traduzir código de erro.',
    'O FastAPI gera automaticamente uma documentação interativa dos endpoints, acessível em /docs quando a API está no ar. Por ela é possível testar cada rota sem escrever código, o que facilita tanto o desenvolvimento quanto a demonstração do projeto.',
  ],
  tabela: [
    ['Módulo', 'Rotas', 'Responsabilidade'],
    ['auth', '11', 'Cadastro, envio dos documentos do cadastro, confirmação por código (e-mail ou SMS), login, recuperação de senha e canais disponíveis'],
    ['admin', '12', 'Painel do administrador: condomínios e usuários da plataforma'],
    ['usuarios', '15', 'Cadastro de porteiros e moradores, aprovação com os documentos do cadastro, permissões e foto de perfil'],
    ['condominios', '5', 'Dados do condomínio, unidades e código de acesso'],
    ['reservas', '10', 'Espaços comuns, agenda sigilosa, reservas e ocupação'],
    ['portaria', '16', 'Visitantes, encomendas e ocorrências, com as fotos de cada um'],
    ['financeiro', '7', 'Preferência de cobrança, cobranças e pagamentos'],
    ['comunicados', '4', 'Publicação, leitura e remoção de avisos'],
    ['veiculos', '4', 'Entradas e saídas do estacionamento e ocupação'],
    ['manutencao', '5', 'Ordens de serviço e indicadores de custo'],
    ['documentos', '4', 'Atas, convenção, regimento e plantas, com o arquivo protegido'],
    ['mensagens', '4', 'Chat entre síndico, porteiros e moradores, com contador de não lidas'],
    ['arquivos', '1', 'Entrega das fotos de perfil enviadas'],
  ],
};

// ── 15 Testes automatizados (nova) ──────────────────────────────────
const testes = {
  paragrafos: [
    'As regras do sistema são verificadas por uma suíte de 329 casos de teste automatizados, escritos com pytest e executados contra um banco PostgreSQL real, e não contra um banco simulado. Assim, restrições de chave estrangeira e de unicidade também são exercitadas.',
    'Os testes não conferem apenas se o caminho feliz funciona. Boa parte deles verifica justamente o que o sistema precisa recusar: um morador não pode ver a ocorrência de outro; um porteiro sem a permissão liberada pelo síndico não consegue registrar uma ocorrência; uma reserva que se sobrepõe a outra é recusada; a mensagem de conflito não revela quem reservou; e a senha nunca é gravada em texto puro.',
    'Uma parte dos testes dispara várias requisições ao mesmo tempo, porque a conferência e a gravação não são um passo só: sem uma trava no banco, quatro moradores pedindo o mesmo horário juntos conseguiam, na maioria das tentativas, reservar o espaço duas vezes. Cada vez que uma regra nova é escrita, um teste correspondente é adicionado. Isso permite alterar o código com segurança: se uma mudança quebrar uma regra antiga, a suíte acusa antes de o problema chegar à tela.',
    'A suíte é executada automaticamente a cada envio de código ao repositório, junto com duas outras verificações: a aplicação das mudanças de estrutura do banco no sentido de ida e de volta, feita com a tabela já populada, que é a situação em que uma alteração mal escrita falha; e a execução dos scripts de criação e carga do banco em um banco vazio, já que eles são mantidos manualmente e podem deixar de acompanhar uma mudança de estrutura.',
    'Além da suíte do servidor, 58 testes de interface abrem as telas em um navegador Chromium real, nos temas claro e escuro, em largura de computador e de celular. Eles conferem o que já falhou uma vez e não pode voltar: erros de JavaScript, imagens quebradas, rolagem lateral no celular, a barra superior fora do topo, títulos e cartões sem ícone, caixas claras no tema escuro, elementos marcados como escondidos que continuavam aparecendo, a logo levando ao painel de cada perfil, o medidor de força da senha, a planilha exportada que não pode transformar um nome digitado em fórmula do Excel e formulário que pede um dado que nenhum código lê — dado pessoal coletado à toa. Cinco deles percorrem os fluxos com arquivo de ponta a ponta: a captura pela câmera, com uma câmera simulada do navegador, a foto tirada pelo porteiro chegando ao painel do morador, a foto da ocorrência chegando ao síndico, os documentos escolhidos no cadastro chegando à fila de aprovação do síndico e o documento publicado pelo síndico abrindo para o morador. Também rodam a cada envio, com o banco, a API e o site no ar.',
    'Por fim, o banco criado pelos scripts SQL manuais é comparado ao banco criado pelas migrações — tabelas, colunas, restrições, índices e tipos —, porque rodar sem erro não garante que o resultado seja o mesmo: um script que esquecesse uma tabela nova rodaria normalmente.',
  ],
  tabela: [
    ['Arquivo de teste', 'Casos', 'O que cobre'],
    ['test_auth.py', '39', 'Cadastro, código de confirmação, login, bloqueio por tentativas e recuperação de senha'],
    ['test_admin.py', '29', 'Painel do administrador e gestão da plataforma'],
    ['test_usuarios.py', '35', 'Hierarquia de cadastro, aprovação com registro de autoria e permissões do porteiro'],
    ['test_operacao.py', '40', 'Veículos, ordens de serviço e documentos do condomínio: envio do arquivo, tipos aceitos e quem pode abrir'],
    ['test_financeiro.py', '36', 'Cobranças, pagamentos e inadimplência'],
    ['test_portaria.py', '27', 'Visitantes, encomendas e ocorrências, e o que o porteiro sem permissão não consulta'],
    ['test_reservas.py', '28', 'Espaços, agenda sigilosa e aprovação de reservas'],
    ['test_notificacao.py', '17', 'Entrega dos códigos por e-mail e por SMS, e o que não pode ir para o log'],
    ['test_foto.py', '12', 'Foto de perfil: tipo conferido pelo conteúdo, tamanho, nome gerado pelo servidor e remoção'],
    ['test_mensagens.py', '11', 'Chat: quem pode conversar com quem, não lidas e mensagens inválidas'],
    ['test_documentos_cadastro.py', '19', 'Documentos do cadastro: autorização de envio, tipos aceitos, acesso só do síndico e descarte na recusa e na inativação'],
    ['test_portaria_fotos.py', '15', 'Fotos de visitantes e encomendas: quem pode ver, tipo conferido e prazo de guarda'],
    ['test_concorrencia.py', '4', 'Requisições simultâneas: o mesmo horário não é reservado duas vezes e a mesma cobrança não é paga a mais'],
    ['test_valores_extremos.py', '11', 'Valores que o banco recusa (id acima do limite, caractere nulo) respondem como dado inválido, e não como falha do servidor'],
    ['test_ocorrencias_fotos.py', '6', 'Foto da ocorrência: só quem abriu anexa, quem pode ver vê e a foto não muda depois da resposta'],
  ],
};

// ── 16 Conclusão ────────────────────────────────────────────────────
const conclusao = [
  'O projeto SmartCondo: Sistema de Gerenciamento de Condomínios, tem como função primordial resolver as dores recorrentes em condomínios de pequeno a médio porte em Campo Grande – MS, com planos de expansão para o âmbito nacional. As principais problemáticas incluem conflitos entre moradores, inconsistências na gestão financeira e falhas na comunicação eficaz.',
  'A implementação do SmartCondo é crucial para elevar a qualidade e praticidade na rotina desses condomínios, trazendo fluidez no setor financeiro e possibilitando a execução de ações rotineiras, como a visualização de espaços em uso. O objetivo é facilitar a operação do gerenciamento, eliminando falhas financeiras e reduzindo significativamente intrigas internas. Para isso, o projeto visa atender a todos os usuários de modo completo e se adequar ao cotidiano, garantindo organização nas moradias e serviços.',
  'O sistema prevê funcionalidades específicas para cada tipo de usuário – administrador, síndico, porteiro e morador. O administrador opera a plataforma, cadastrando os condomínios e criando a conta do síndico de cada um. O síndico poderá gerenciar de forma prática e eficiente, incluindo o gerenciamento financeiro com notificações de pagamento e a visualização remota e sigilosa da locação de espaços. O porteiro terá recursos para notificar entregas, registrar entradas e saídas e utilizar o videoporteiro para confirmar a entrada de convidados com foto ou gravação em tempo real, fomentando a segurança. O morador poderá realizar pagamentos com opções variadas, alugar espaços de forma sigilosa, verificar a ocupação de áreas comuns e receber notificações e confirmações de entregas/convidados.',
  'Com um prazo de 2 anos, o projeto se baseia na utilização de linguagens e ferramentas robustas e escaláveis, como HTML, CSS e JavaScript no front-end, Python com FastAPI no back-end e PostgreSQL no banco de dados. Adicionalmente, o projeto demonstra um compromisso com a acessibilidade, utilizando VLibras para usuários com deficiência auditiva, e recursos de alteração de tamanho de fonte e mudança de cores (modo claro/escuro) para deficiências visuais, garantindo uma boa experiência e inclusão.',
  'Até o momento, o sistema conta com as quatro áreas de acesso implementadas e ligadas à API, 21 tabelas em PostgreSQL, 99 endpoints, 329 casos de teste automatizados cobrindo as regras de negócio e 58 testes de interface executados em um navegador real.',
  'Em suma, o SmartCondo é um projeto realista, alinhado com as necessidades do mercado e da tecnologia atual, visando transformar a gestão de condomínios de pequeno e médio porte em um processo ágil, prático, seguro e inclusivo.',
];

// ── 17 Cronograma ───────────────────────────────────────────────────
const cronograma = [
  ['Fase', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
  ['1ª Fase', 'Detalhamento de Requisitos e Arquitetura', 'Detalhamento de Requisitos e Arquitetura', 'Protótipos de Telas no Figma', 'Protótipos de Telas no Figma', 'Desenvolvimento Front-end (HTML/CSS)'],
  ['2ª Fase', 'Desenvolvimento Front-end (HTML/CSS)', 'Desenvolvimento Front-end (JavaScript)', 'Desenvolvimento Back-end (Python)', 'Desenvolvimento Back-end (Python)', 'Integração/Testes Iniciais'],
  ['3ª Fase', 'Desenvolvimento de Funcionalidades Chave (Pagamento, Reserva)', 'Implementação de Segurança e VLibras/Acessibilidade', 'Testes e Correção de Bugs', 'Treinamento dos Usuários Operacionais (Porteiro/Síndico)', 'Implantação Piloto (Campo Grande - MS)'],
  ['4ª Fase', 'Teste Piloto e Coleta de Feedback (Síndico/Gerente)', 'Ajustes Finais do Sistema (Pós-Feedback)', 'Lançamento e Suporte Contínuo', 'Avaliação de Expansão Nacional', 'Expansão e Novas Funcionalidades (Início do 2º ano)'],
];

// ── 18 Referências ──────────────────────────────────────────────────
const referencias = [
  'PRESSMAN, Roger S. Engenharia de Software: uma abordagem profissional. 8. ed. Porto Alegre: AMGH, 2016.',
  'SOMMERVILLE, Ian. Engenharia de Software. 10. ed. São Paulo: Pearson, 2018.',
  'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 14724: informação e documentação — trabalhos acadêmicos — apresentação. Rio de Janeiro: ABNT, 2011.',
  'BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018.',
  'WORLD WIDE WEB CONSORTIUM. Web Content Accessibility Guidelines (WCAG) 2.2. W3C Recommendation, 2023. Disponível em: https://www.w3.org/TR/WCAG22/.',
  'FASTAPI. FastAPI documentation. Disponível em: https://fastapi.tiangolo.com/.',
  'THE POSTGRESQL GLOBAL DEVELOPMENT GROUP. PostgreSQL 16 Documentation. Disponível em: https://www.postgresql.org/docs/16/.',
  'VLIBRAS. Suíte VLibras. Ministério da Gestão e da Inovação em Serviços Públicos. Disponível em: https://www.gov.br/governodigital/pt-br/vlibras.',
];

module.exports = { acessibilidade, arquitetura, api, testes, conclusao, cronograma, referencias };
