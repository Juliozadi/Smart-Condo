/* Conteúdo da documentação do SmartCondo.
 *
 * O texto das seções 1 a 9, 10, 12, 13 (conclusão), 14 (cronograma) e 15
 * (referências) é o do documento original do grupo, transcrito do PDF.
 * As alterações feitas estão anotadas em ALTERACOES.md.
 */

// ── Capa ────────────────────────────────────────────────────────────
const capa = {
  titulo: 'Sistema de Gerenciamento de Condomínios',
  integrantes: [
    'Júlio Zadi',
    'Luan Flôres Martins',
    'Lenini Bellodi Júnior',
    'Juliano Araujo',
    'João Victor Muller Miranda',
  ],
  disciplina: 'Projeto Integrador I',
  ano: '2025',
};

// ── Seções 1 a 10: texto original ───────────────────────────────────
const secoes = [
{ n: '1', titulo: 'INTRODUÇÃO', paragrafos: [
  'Este documento tem como função principal, iniciar o projeto de Desenvolvimento do Sistema de Gerenciamento de Condomínios para diversos usuários em Campo Grande – MS e, posteriormente, no âmbito nacional. Será utilizado para detalhar as justificativas que torna o projeto necessário, um sistema eficiente, como suas funcionalidades principais e partes que envolvem o processo.',
  'Este documento, também funda os critérios para o sucesso do sistema de gerenciamento, delimitando requisitos, recursos, prazos e responsabilidades, assegurando que a modelagem seja concretizada de modo eficaz e alinhado com as necessidades dos condomínios de pequeno a médio porte. O Sistema de Gerenciamento de Condomínios, deve promover agilidade e praticidade em processos rotineiros, típicos de condomínios, assegurando uma gestão de qualidade.',
]},

{ n: '2', titulo: 'IDENTIFICAÇÃO DO PROJETO', paragrafos: [
  'Projeto: SmartCondo: Gestão de condomínios',
  'Gestor do Projeto: Júlio Zadi',
]},

{ n: '3', titulo: 'JUSTIFICATIVA', paragrafos: [
  'Atualmente, condomínios de pequeno a médio porte, passam por problemas internos constantes, como conflitos entre moradores, inconstâncias no gerenciamento financeiro por parte do síndico ou funcionário administrativo. Existe também, outra causa recorrente sobre problemas nos condomínios, que seria ela a falta de comunicação de modo prático e eficaz, levando a insatisfações por exemplo quando um espaço está alugado por um morador e, outro residente encontra discordância pois queria alugar o mesmo espaço.',
  'A repetição dos problemas, gera ao longo do tempo, um ambiente de difícil convivência para ambas as partes, agravando comportamentos e podendo até mesmo levar um condomínio a ser pouco habitado pela sua imagem malvista devido à baixa qualidade da gestão.',
  'Contudo, a implementação do SmartCondo, o Sistema de Gerenciamento de Condomínios, é sem dúvidas, essencial para chegarmos a um próximo patamar de qualidade e praticidade no cotidiano de condomínios pequenos a médio porte. Visto, que o sistema trará a possibilidade de executar tanto ações rotineiras como apresentar que um espaço já está em uso ou quantas pessoas estão lá, como também no setor financeiro, promovendo fluidez e a ascensão de condomínios que antes estavam em declínio pela baixa qualidade da gestão, como dito anteriormente.',
]},

{ n: '4', titulo: 'OBJETIVO DO PROJETO', paragrafos: [
  'O objetivo da implementação do SmartCondo, Sistema para Gerenciamento de Condomínios, busca facilitar o modo em que os condomínios operam no gerenciamento, eliminando falhas no financeiro e diminuindo consideravelmente intrigas internas entre moradores e até entre moradores e funcionários.',
  'O projeto tem como foco também, garantir que todos estejam sendo atendidos de modo completo, evitando boa parte de infortúnios após a implementação do sistema. Como sendo um projeto realista, visa se adequar no cotidiano e garantir organização nas moradias e serviços.',
  'Considerando o atual mercado e tecnologia, o prazo do projeto determinado é de 2 anos. Sendo nesse período viável com os recursos e prazos estabelecidos.',
]},

{ n: '5', titulo: 'RESPONSABILIDADES E PARTES INTERESSADAS', paragrafos: [
  'A execução do projeto do Gerenciamento de Condomínios SmartCondo, envolve os condomínios de pequeno a médio porte como interessados. Envolve também as divisões executoras do projeto, cada uma com sua responsabilidade para assegurar o sucesso do projeto.',
  { negritoAte: 'Síndico do Condomínio:', texto: 'Síndico do Condomínio: testar o sistema durante certo período e avaliar a evolução em sua organização e redução de problemas internos. Será o principal responsável pela avaliação durante o período de teste da plataforma.' },
  { negritoAte: 'Porteiro:', texto: 'Porteiro: responsável por utilizar o sistema na recepção de pedidos e encomendas dos moradores, entrada e saídas de moradores.' },
  { negritoAte: 'Equipe de TI:', texto: 'Equipe de TI: responsável pela implementação e configuração técnica do sistema de Gerenciamento de Condomínios. Está equipe será responsável também por oferecer suporte técnico e treinamento aos usuários operacionais e garantir que o sistema funcione de modo fluído após a implementação.' },
  'A equipe de vendas e o Gerente do projeto serão responsáveis por receber os feedbacks do sistema de seus usuários, que irão contribuir com críticas ou satisfação.',
]},

{ n: '6', titulo: 'HISTÓRIA DO USUÁRIO', paragrafos: [
  'Como Síndico, quero poder gerenciar de modo prático e eficiente as ações de meus clientes, os moradores. Preciso que, em vez de constantemente enviar cobranças via Whatsapp (aplicativo de mensagens) ou outros meios, gostaria que um sistema fizesse por mim, e, quando o pagamento for efetuado, o próprio sistema me notificar com qual meio o pagamento foi realizado, por quem e a data do pagamento.',
  'Quero também, que meus clientes possam visualizar remotamente sem precisarem de mim ou funcionário, se um local do condomínio está ou não alugado para certa data. Por exemplo, meu cliente alugou a “área de confraternizações na data --/-- das 14:00 até 21:30”, no sistema para o cliente, irá mostrar que está em ocupação nesta data e horário, e eu gostaria que não mostrasse quem alugou, para evitar conflitos. Caso esteja disponível, por ordem de chegada ou antecipação, o espaço será alugado. Quero também, para espaços públicos dentro do condomínio, que mostre quantos indivíduos estão ocupando a área no momento, por exemplo “Piscina: 23 pessoas no momento”.',
  'Como porteiro, gostaria que o sistema enviasse uma notificação de entrega para o cliente que realizou o pedido, seja um item importado, pedido em restaurante, ou móveis etc.',
  'Seria interessante que ao chegar na portaria, e um indivíduo dissesse que é um convidado, seja de funcionário ou cliente, que uma notificação seja enviada para o cliente com a foto do indivíduo ou gravação em tempo real (vídeo porteiro), para que ele seja identificado e, assim, o cliente confirme se é ou não seu convidado, fornecendo dados e fomentando a segurança antes de adentrar o condomínio.',
  'Como morador, gostaria que o software fizesse uma cobrança mensal na data em que eu escolhesse, que me desse variadas opções para formas de pagamento. Acharia interessante que existisse opções práticas para alugar espaços do condomínio, e gostaria que fosse sigiloso, para que outro morador não viesse me questionar sobre minha escolha, evitando conflito. Sobre espaços dos condomínios, uma opção de visualizar quantas pessoas estão no lugar atualmente, seria de grande ajuda.',
  'Por fim, o sistema poderia me notificar de entregas ou pedidos que eu fiz, assim, o porteiro me envia pelo sistema uma foto ou vídeo para que eu confirmasse a minha entrega ou pedido. De modo parecido, se parentes, amigos, ou convidados viessem me visitar, eu gostaria de ver uma foto ou vídeo em tempo real do convidado. Isso me ajudaria a confirmar se é realmente um convidado e na segurança não apenas individual, mas de todos que habitam o condomínio.',
]},

{ n: '7', titulo: 'IDENTIFICAÇÃO DOS REQUISITOS', paragrafos: [
  'Os requisitos são referenciados por um identificador fixo, que não muda ao longo do projeto mesmo que a ordem das seções mude. Requisitos funcionais recebem a sigla RF seguida de três dígitos; requisitos não funcionais recebem RNF seguido de três dígitos.',
  'O requisito [Cadastrar condomínio, RF001] está descrito na seção "Requisitos Funcionais", no bloco identificado por RF001. O requisito não funcional [Autenticação por token, RNF009] está descrito na seção "Requisitos Não Funcionais", na subseção de segurança, no bloco identificado por RNF009.',
  'Cada bloco traz os atores envolvidos, a prioridade, a descrição do que o sistema faz, as entradas e pré-condições necessárias e as saídas e pós-condições resultantes. A prioridade segue três níveis: essencial, quando o sistema não cumpre seu objetivo sem o requisito; importante, quando a ausência prejudica o uso mas não o impede; e desejável, quando acrescenta conveniência.',
]},

{ n: '8', titulo: 'DESCRIÇÃO DOS USUÁRIOS', paragrafos: [
  { negritoAte: 'Administrador:', texto: 'Administrador: responsável por operar a plataforma. Cadastra os condomínios e, dentro de cada um deles, cria a conta do síndico. Também pode criar, editar e remover porteiros e moradores de qualquer condomínio, servindo de apoio quando o síndico não consegue resolver algo sozinho.' },
  { negritoAte: 'Síndico:', texto: 'Síndico: responsável pelo cadastro dos funcionários (sendo porteiro ou alguma outra área do condomínio), administrar os moradores, supervisionar quando necessário a parte financeira do sistema, por fim, emitir avisos e notificações importantes sobre o condomínio.' },
  { negritoAte: 'Porteiro:', texto: 'Porteiro: responsável por realizar a permissão de entrada de convidados com o vídeo porteiro ou enviando fotos de confirmação para o morador que convidou, anotar pedidos ou entregas dos moradores e, enviar notificações para os moradores de seus pedidos ou entregas.' },
  { negritoAte: 'Morador:', texto: 'Morador: utilizar do sistema para fazer o pagamento, verificar se há possibilidade de alugar um espaço, verificar quantas pessoas tem em um lugar do condomínio, realizar e receber chamados do síndico ou porteiro quando necessário.' },
]},
];

// ── Histórico de revisões ───────────────────────────────────────────
// Vai logo depois da capa, como no modelo: quem mexeu, quando e no quê.
const historico = [
  ['Data', 'Versão', 'Descrição', 'Autores'],
  ['21/09/2026', '1.0', 'Versão inicial da documentação do projeto',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['22/09/2026', '1.1', 'Acessibilidade e contraste, bloqueio de login por tentativas e tratamento de dados pessoais',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['22/09/2026', '2.0', 'Requisitos funcionais e não funcionais numerados, diagrama de casos de uso, modelo e diagrama entidade-relacionamento, relacionamentos, dicionário de dados e implementações no banco',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['23/09/2026', '2.1', 'Foto de perfil, chat e ligação, envio de código por SMS, testes de interface e comparação dos scripts SQL com as migrações',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['23/09/2026', '2.2', 'Fotos de visitantes e encomendas com acesso restrito e prazo de guarda, e documentos do cadastro do morador conferidos pelo síndico',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['24/09/2026', '2.3', 'Foto da ocorrência, consultas do porteiro limitadas às permissões, limite de envio de códigos e correções da revisão geral',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['24/09/2026', '2.4', 'Documentos do condomínio enviados como arquivo pelo síndico, com acesso restrito, e validação das datas e dos endereços informados',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
  ['25/09/2026', '2.5', 'Vários administradores, histórico de quem fez cada alteração e inativação no lugar da exclusão; sai o complemento do cadastro de condomínio',
   'Júlio Zadi, Luan Flôres Martins, Lenini Bellodi Júnior, Juliano Araujo, João Victor Muller Miranda'],
];

// ── Seção 9: casos de uso ───────────────────────────────────────────
const casosDeUso = [
  {
    nome: 'Cadastro',
    principal: 'Administrador, síndico ou morador',
    resumo: 'Cadastro do síndico, do porteiro ou do morador, conforme o nível de acesso de quem cadastra',
    prerequisitos: null,
    sistema: [
      '2 O sistema pede as informações para cadastro, de acordo com quem está sendo cadastrado',
      '4 O sistema salva e envia um código de confirmação pelo meio escolhido',
    ],
    usuario: [
      '1 O usuário escolhe quem irá cadastrar, dentro do que o seu nível de acesso permite',
      '3 O usuário digita as informações',
      '5 O usuário faz a validação de seu cadastro.',
    ],
    nota: 'O cadastro segue a hierarquia do sistema: o administrador cria a conta do síndico junto com o condomínio; o síndico cadastra os porteiros e os moradores do seu condomínio; e o morador também pode se cadastrar sozinho, informando o código de acesso do condomínio. Nesse último caso o cadastro fica aguardando a aprovação do síndico antes de liberar o acesso.',
  },
  {
    nome: 'Login do usuário',
    principal: 'Administrador, síndico, porteiro ou morador',
    resumo: 'Efetuar a sessão do usuário',
    prerequisitos: 'Ter realizado o cadastro.',
    sistema: ['1 O sistema pede as informações para o login', '3 O sistema valida as credenciais', '4 Login efetuado.'],
    usuario: ['2 O usuário insere as informações'],
  },
  {
    nome: 'Esqueci minha senha',
    principal: 'Administrador, síndico, porteiro ou morador',
    resumo: 'Recuperar senha ou acesso perdido do usuário',
    prerequisitos: 'Ter um cadastro existente',
    sistema: [
      '2 O sistema pede as informações para recuperação',
      '5 O sistema envia um código pelo meio escolhido pelo usuário e informa que o código deve ser inserido no campo para conclusão da recuperação',
    ],
    usuario: [
      '1 O usuário clica no botão esqueci minha senha',
      '3 O usuário digita as informações',
      '4 O usuário confirma e envia solicitação',
      '6 O usuário digita o código recebido e redefine sua senha.',
    ],
  },
  {
    nome: 'Cadastro do condomínio',
    principal: 'Administrador',
    resumo: 'Cadastrar o condomínio no sistema e vincular o síndico responsável',
    prerequisitos: 'Existir um administrador ativo',
    sistema: [
      '1 O sistema pede as informações para o cadastro',
      '3 O sistema valida as informações e gera o código de acesso do condomínio',
      '4 Cadastro concluído',
    ],
    usuario: ['2 O administrador insere as informações'],
    nota: 'O código de acesso gerado é o que o síndico repassa aos moradores para que eles possam se cadastrar sozinhos no condomínio certo.',
  },
  {
    nome: 'Permissão do Porteiro',
    principal: 'Síndico',
    resumo: 'Permitir ações do porteiro no sistema',
    prerequisitos: 'Existir um síndico ativo',
    sistema: ['1 O sistema mostra as possibilidades de ações do porteiro', '3 O sistema atende e faz a conclusão.'],
    usuario: ['2 O síndico escolhe quais estarão disponíveis para o porteiro'],
  },
];

module.exports = { capa, historico, secoes, casosDeUso };
