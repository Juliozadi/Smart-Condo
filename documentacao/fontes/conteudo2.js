/* Seções 10 a 18. O texto das seções 10, 12 (acessibilidade), 16
 * (conclusão), 17 (cronograma) e 18 (referências) vem do documento
 * original; as seções 13, 14 e 15 são novas. */

// ── 10 Linguagens e ferramentas ─────────────────────────────────────
const ferramentas = {
  intro: 'A escolha das linguagens se deu pela usabilidade e escalabilidade necessária para o projeto, tendo em vista o visível crescimento do número de usuários e a agilidade demandada pelos setores residenciais.',
  itens: [
    { n: '10.1', nome: 'HTML', texto: 'Linguagem de Marcação de Hipertexto, é a base para a criação de páginas da web, utilizada para estruturar o todo conteúdo visível do projeto por meio das tags, textos e elementos estruturais.' },
    { n: '10.2', nome: 'CSS', texto: '(Cascading Style Sheets) é uma linguagem de estilo usada para descrever a apresentação de documentos, será usada para estilizar toda a estrutura do projeto, garantindo uma boa experiência para o usuário por meio de recursos intuitivos e aparência moderna, priorizando a responsividade da aplicação.' },
    { n: '10.3', nome: 'JavaScript', texto: 'É a linguagem de script mais usada no desenvolvimento web, funcionando principalmente no navegador do cliente (front-end) para manipular elementos HTML e CSS. Com o JavaScript, introduziremos animações de tela intuitivas e faremos a manipulação de elementos HTML e CSS, promovendo uma interface amigável. No SmartCondo o front-end foi escrito em JavaScript puro, sem frameworks nem bibliotecas externas.' },
    { n: '10.4', nome: 'Python', texto: 'Python é uma linguagem de programação de alto nível, simples e de fácil leitura, muito utilizada no desenvolvimento web, automação e análise de dados. Possui uma vasta biblioteca padrão e frameworks poderosos que agilizam o desenvolvimento do backend. Sua sintaxe clara facilita a manutenção do código e o trabalho em equipe. Além disso, é multiplataforma e tem excelente integração com bancos de dados e APIs. Em um projeto de gestão de condomínios, Python permite criar sistemas seguros, escaláveis e com rotinas automatizadas, como geração de boletos e envio de notificações. Sua comunidade ativa garante suporte e atualizações constantes. Por isso, é uma das melhores escolhas para o backend de aplicações modernas.' },
    { n: '10.5', nome: 'PostgreSQL', texto: 'O PostgreSQL é um sistema de gerenciamento de banco de dados relacional, open source e altamente confiável. Suporta consultas complexas, transações seguras e integrações com diversas linguagens. É ideal para armazenar e gerenciar grandes volumes de dados estruturados, garantindo consistência e desempenho. No projeto de gestão de condomínios, o PostgreSQL será responsável pelo armazenamento dos cadastros, registros financeiros e reservas de espaços. Sua robustez e escalabilidade tornam-o a escolha ideal para aplicações corporativas modernas.' },
    { n: '10.6', nome: 'FastAPI', texto: 'FastAPI é o framework Python escolhido para construir a API REST do SmartCondo. Ele gera automaticamente a documentação interativa dos endpoints e valida os dados que entram e saem da aplicação a partir dos modelos declarados, o que reduz a chance de um dado inválido chegar ao banco. É também um dos frameworks Python mais rápidos disponíveis, por trabalhar de forma assíncrona.' },
    { n: '10.7', nome: 'SQLAlchemy e Alembic', texto: 'O SQLAlchemy é a camada que traduz as tabelas do PostgreSQL em classes Python, permitindo escrever as consultas no próprio código e trocando o SQL manual por objetos. O Alembic acompanha o SQLAlchemy e cuida das migrações: cada mudança na estrutura do banco vira um arquivo versionado, de modo que qualquer integrante do grupo consegue atualizar o próprio banco com um único comando e voltar atrás se necessário.' },
    { n: '10.8', nome: 'Figma', texto: 'Ferramenta de design online e colaborativa usada para criar interfaces de sites, aplicativos e produtos digitais. É a base de todo o design e estrutura front-end a ser desenvolvida no nosso projeto.' },
  ],
};

// ── 11 Prototipação das telas ───────────────────────────────────────
// A numeração de 11.1 a 11.7.3 é a do documento original e foi mantida,
// porque o código-fonte faz referência a ela em comentários.
const telas = [
  { n: '11.1', titulo: 'Tela de cadastro',
    texto: 'A tela de cadastro do usuário tem como função principal pedir a opção de quem será cadastrado, e logo após exigir as credenciais. Com a hierarquia do sistema, o cadastro aberto ao público é apenas o do morador: o síndico é criado pelo administrador e o porteiro é criado pelo síndico.',
    imagem: 'cadastro-escolha.png', legenda: 'Tela de escolha do tipo de cadastro' },

  { n: '11.2', titulo: 'Tela de cadastro do porteiro',
    texto: 'O cadastro do porteiro deve ser fomentado com dados pessoais, e por fim as permissões de uso no sistema. Quem realiza esse cadastro é o síndico do condomínio.',
    imagem: 'sindico-porteiros.png', legenda: 'Gestão de porteiros, com o painel de permissões de cada um' },

  { n: '11.3', titulo: 'Tela de cadastro morador',
    texto: 'A tela de cadastro do morador, inicialmente, vai pedir as credenciais, após registradas, o sistema salva e parte para a próxima etapa, que irá requisitar nome do condomínio, o bloco/torre, e o vínculo dele com o estabelecimento. No fim, o Acesso e Segurança, com o envio dos documentos que comprovam esse vínculo (RG ou CNH e comprovante de residência) e a criação da senha, e por último, a conclusão. O morador informa o código de acesso do condomínio, fornecido pelo síndico, para que o cadastro seja vinculado ao condomínio correto.',
    imagem: 'cadastro-morador.png', legenda: 'Cadastro do morador, dividido em etapas' },

  { n: '11.4', titulo: 'Tela de login',
    texto: 'A tela de login é a porta de entrada do sistema e é comum aos quatro perfis. Após validar as credenciais, o sistema identifica o papel do usuário e o encaminha para o painel correspondente. A tela também dá acesso à recuperação de senha e ao cadastro do morador.',
    imagem: 'login.png', legenda: 'Tela de login' },

  { n: '11.5', titulo: 'Telas do Síndico', texto: null, imagem: null },
  { n: '11.5.1', titulo: 'Tela inicial',
    texto: 'A tela inicial do Síndico, dashboard, vai conter a opção de todas informações que ele tem direito de manipular e observar, sendo elas financeiro, reservas de espaços, comunicados, moradores e porteiros. O painel também reúne, no topo, o que está pendente de decisão: cadastros aguardando aprovação, reservas a avaliar, unidades em atraso e ocorrências em aberto.',
    imagem: 'sindico-dashboard.png', legenda: 'Painel do síndico' },
  { n: '11.5.2', titulo: 'Visualizar porteiros',
    texto: 'Nesta tela, o síndico pode visualizar todos porteiros ativos ou de folga no momento. Assim como também pode contatá-los por chat ou ligação de voz. É também aqui que ele define, por porteiro, quais ações ficam liberadas no sistema.',
    imagem: 'sindico-porteiros.png', legenda: 'Equipe de portaria e permissões' },
  { n: '11.5.3', titulo: 'Tela de histórico e aprovação de espaços',
    texto: 'Na tela de histórico e aprovação de espaços, o Síndico pode aprovar se o morador pode ou não alugar o espaço e pode ver anteriormente o que foi alugado. Ao recusar, o síndico informa o motivo, que é exibido ao morador.',
    imagem: 'sindico-reservas.png', legenda: 'Aprovação de reservas' },
  { n: '11.5.4', titulo: 'Tela de comunicados',
    texto: 'Na tela de comunicados, o Síndico pode fazer comunicados sobre qualquer assunto que lhe vê importância de repassar aos moradores. O comunicado vai para todos os moradores do condomínio e pode ser fixado no topo da lista.',
    imagem: 'sindico-comunicados.png', legenda: 'Publicação de comunicados' },
  { n: '11.5.5', titulo: 'Tela financeira',
    texto: 'Reúne os indicadores do condomínio — total recebido, em aberto, vencido e quantas unidades estão em atraso — e permite gerar a cobrança mensal de todas as unidades de uma vez. Cada cobrança usa o dia de vencimento que o próprio morador escolheu.',
    imagem: 'sindico-financeiro.png', legenda: 'Gestão financeira do condomínio' },
  { n: '11.5.6', titulo: 'Tela de manutenção',
    texto: 'Permite abrir ordens de serviço com tipo, prioridade, local, fornecedor e custo estimado, e acompanhar cada uma até a conclusão, registrando o custo real gasto.',
    imagem: 'sindico-manutencao.png', legenda: 'Ordens de serviço' },
  { n: '11.5.7', titulo: 'Tela de ocorrências',
    texto: 'Lista os chamados abertos por moradores e porteiros, ordenados pelo que ainda está em aberto e pela urgência. O síndico responde e muda a situação da ocorrência, e a resposta aparece para quem abriu.',
    imagem: 'sindico-ocorrencias.png', legenda: 'Ocorrências do condomínio' },

  { n: '11.6', titulo: 'Telas do Morador', texto: null, imagem: null },
  { n: '11.6.1', titulo: 'Tela inicial (Dashboard)',
    texto: 'A tela inicial do morador exibe uma saudação com o nome do usuário, o nome do condomínio e atalhos principais para reservas, financeiro e comunicados. Também mostra um resumo das próximas reservas e dos últimos avisos do síndico, além de uma barra inferior de navegação para facilitar o acesso às demais funções. No topo aparece a portaria: é onde o morador confirma ou recusa o visitante e a encomenda registrados pelo porteiro.',
    imagem: 'morador-dashboard.png', legenda: 'Painel do morador, com as confirmações da portaria' },
  { n: '11.6.2', titulo: 'Tela de Faturas / Financeiro',
    texto: 'Nesta tela o morador acompanha boletos e pagamentos do condomínio. É possível visualizar faturas pagas, pendentes ou vencidas, ver detalhes e registrar o pagamento pela forma escolhida. O morador também define aqui o dia do vencimento e o meio de pagamento que prefere, que é o que o síndico usa ao gerar a cobrança do mês.',
    imagem: 'morador-financeiro.png', legenda: 'Financeiro do morador' },
  { n: '11.6.3', titulo: 'Tela de Reservas de Espaços',
    texto: 'Permite ao morador reservar áreas comuns como salão, churrasqueira e piscina. O usuário escolhe data e horário, adiciona observações e acompanha o status das reservas (pendente, aprovada ou recusada). Ao escolher o espaço e a data, o sistema avisa quais horários já estão ocupados, sem revelar quem reservou. A tela mostra ainda a ocupação em tempo real das áreas de uso livre.',
    imagem: 'morador-reservas.png', legenda: 'Reservas e ocupação das áreas comuns' },
  { n: '11.6.4', titulo: 'Tela de Comunicados',
    texto: 'Reúne avisos e comunicados enviados pelo síndico. O morador pode buscar, filtrar por categoria e visualizar o conteúdo completo de cada mensagem, marcando-as como lidas.',
    imagem: 'morador-comunicados.png', legenda: 'Comunicados recebidos pelo morador' },
  { n: '11.6.5', titulo: 'Tela de Documentos',
    texto: 'Dá acesso aos documentos do condomínio — convenção, regimento interno, atas de assembleia e prestações de conta — além dos documentos da própria unidade, como a planta baixa. A busca e o filtro por categoria facilitam localizar um arquivo específico. Os arquivos são enviados pelo síndico na tela de documentos do painel dele e abrem numa aba nova, baixados com o token de quem está conectado.',
    imagem: 'morador-documentos.png', legenda: 'Documentos do condomínio' },
  { n: '11.6.6', titulo: 'Tela de Ocorrências',
    texto: 'Permite ao morador registrar um incidente informando o tipo, a prioridade, o local e a descrição, e acompanhar a resposta do síndico. Cada morador vê apenas as ocorrências que ele mesmo abriu.',
    imagem: 'morador-ocorrencias.png', legenda: 'Registro e acompanhamento de ocorrências' },
  { n: '11.6.7', titulo: 'Tela de Perfil',
    texto: 'Mostra os dados do cadastro e permite alterar nome, telefone e data de nascimento, além de trocar a senha. CPF e e-mail aparecem apenas para leitura, porque o e-mail é o login e o CPF identifica o cadastro. Os dados da unidade também são de leitura: quem os altera é o síndico.',
    imagem: 'morador-perfil.png', legenda: 'Perfil do morador' },

  { n: '11.7', titulo: 'Telas do Porteiro', texto: null, imagem: null },
  { n: '11.7.1', titulo: 'Tela inicial (Dashboard)',
    texto: 'A tela inicial do porteiro mostra os principais atalhos do sistema, como registro de visitantes, registro de encomendas e comunicados do síndico. Também exibe o número de visitantes presentes, encomendas pendentes e veículos no pátio.',
    imagem: 'porteiro-dashboard.png', legenda: 'Painel do porteiro' },
  { n: '11.7.2', titulo: 'Tela de Registro de Visitantes',
    texto: 'Permite registrar entradas e saídas de visitantes com nome, documento, morador visitado e horário. Mostra a lista de visitantes ativos para controle de acesso. Ao registrar, o morador da unidade recebe a notificação com a foto do vídeo porteiro e precisa confirmar ou recusar a entrada antes que o visitante seja liberado.',
    imagem: 'porteiro-visitantes.png', legenda: 'Controle de visitantes' },
  { n: '11.7.3', titulo: 'Tela de Registro de Encomendas',
    texto: 'Usada para registrar entregas recebidas. Contém nome do destinatário, descrição do pacote e data de recebimento. As encomendas ficam listadas até serem retiradas, e o selo indica há quantos dias o volume está parado na portaria. Quem confirma a retirada é o próprio morador, pelo painel dele.',
    imagem: 'porteiro-encomendas.png', legenda: 'Controle de encomendas' },
  { n: '11.7.4', titulo: 'Tela de Controle de Veículos',
    texto: 'Registra a entrada e a saída de veículos do estacionamento, identificando se é morador, visitante ou prestador. A tela mostra a ocupação do estacionamento e quais veículos estão no pátio no momento.',
    imagem: 'porteiro-veiculos.png', legenda: 'Controle de veículos' },

  { n: '11.8', titulo: 'Telas do Administrador', texto: 'O administrador opera a plataforma como um todo. É ele quem cadastra os condomínios e cria a conta do síndico de cada um. Pode haver mais de um administrador, e cada alteração que eles fazem fica registrada com o autor e o momento: cada linha das listas mostra, por exemplo, "Editado por Fulano em 25/09/2026 14:32", e a janela de edição traz o histórico completo. Nada é apagado: o que é excluído é inativado, e pode ser reativado.', imagem: null },
  { n: '11.8.1', titulo: 'Tela inicial (Dashboard)',
    texto: 'Reúne os indicadores da plataforma: quantos condomínios estão cadastrados e quantos usuários existem em cada papel.',
    imagem: 'admin-dashboard.png', legenda: 'Painel do administrador' },
  { n: '11.8.2', titulo: 'Tela de Condomínios',
    texto: 'Permite cadastrar, editar, inativar e reativar condomínios. Cada condomínio recebe um código de acesso, que é o que o síndico repassa aos moradores para o cadastro; o condomínio inativo aparece no fim da lista, com o código suspenso.',
    imagem: 'admin-condominios.png', legenda: 'Gestão de condomínios' },
  { n: '11.8.3', titulo: 'Tela de Usuários',
    texto: 'Lista todos os usuários da plataforma, com busca e filtros por condomínio, papel e situação. É por aqui que o administrador cria a conta do síndico e de outros administradores e, quando necessário, dá suporte criando, corrigindo, inativando ou reativando porteiros e moradores.',
    imagem: 'admin-usuarios.png', legenda: 'Gestão de usuários' },
];

module.exports = { ferramentas, telas };
