/* Textos das seções de banco de dados.
 *
 * Aqui ficam apenas os textos. A lista de tabelas, colunas, tipos e
 * relacionamentos é gerada por diagramas/dicionario.py, lida do banco em
 * funcionamento, e entra no documento pelo arquivo banco_gerado.js — de
 * modo que o dicionário de dados nunca fica defasado.
 */

const modeloEntidadeRelacionamento = {
  paragrafos: [
    'O modelo de dados do SmartCondo parte de uma decisão que atravessa todo o sistema: a plataforma atende vários condomínios ao mesmo tempo, e nenhum deles pode enxergar os dados do outro. Por isso quase toda entidade carrega, direta ou indiretamente, o vínculo com um condomínio, e toda consulta parte desse vínculo em vez de confiar apenas no identificador informado pela tela.',
    'A hierarquia tem três níveis. O condomínio é a raiz. Dele descem as unidades, que são os apartamentos ou casas. Das unidades descem os moradores. Porteiros e síndicos ligam-se ao condomínio sem passar pela unidade, porque trabalham no condomínio inteiro e não em uma unidade específica. O administrador da plataforma não pertence a condomínio nenhum, e é o único papel nessa condição.',
    'Em volta desse núcleo estão os assuntos do dia a dia, cada um com suas entidades próprias: espaços comuns e reservas; comunicados e as leituras de cada um; documentos; ocorrências e ordens de serviço; cobranças e pagamentos; o movimento da portaria, com visitantes, encomendas e veículos; e as mensagens do chat, trocadas entre duas pessoas do mesmo condomínio.',
    'Duas entidades existem por motivo de segurança, e não por regra de negócio. A de códigos de verificação guarda o resumo criptográfico dos códigos de confirmação e de recuperação de senha, com prazo de validade e contagem de tentativas. A de permissões do porteiro guarda, porteiro a porteiro, o que o síndico liberou — decisão que é do condomínio, e por isso precisa estar gravada, e não fixada no código.',
    'Três escolhas de modelagem merecem registro. A primeira: nenhum registro operacional é apagado quando um usuário sai. A saída inativa a conta, e as ocorrências, encomendas e movimentações que a pessoa gerou continuam no histórico, com o vínculo preservado. A segunda: as entidades que passam por avaliação — o cadastro do morador e a reserva do espaço — guardam quem avaliou, quando e, na recusa, por quê; sem isso a tela de espera só conseguiria dizer que o pedido foi negado, sem explicar. A terceira: a leitura de comunicado é uma entidade própria, com restrição de unicidade por usuário e comunicado, em vez de um campo de contagem — assim o síndico sabe quem leu, e não apenas quantos.',
  ],
};

const relacionamentos = {
  paragrafos: [
    'Os relacionamentos abaixo são as chaves estrangeiras efetivamente declaradas no banco. Todas são do tipo um-para-muitos, lidas da direita para a esquerda: um condomínio tem muitas unidades, uma unidade tem muitos moradores, uma cobrança tem muitos pagamentos.',
    'Declarar o relacionamento no banco, e não apenas no código, tem uma consequência prática: o próprio banco recusa um registro órfão. Não é possível gravar uma reserva apontando para um espaço que não existe, nem uma cobrança de uma unidade que foi removida. A regra vale mesmo que alguém acesse os dados por fora do sistema.',
    'Dois relacionamentos apontam para a mesma tabela de onde saem. Em usuários, o vínculo de quem avaliou o cadastro aponta para outro usuário — o síndico. Em condomínios, o vínculo do síndico responsável aponta para a tabela de usuários, que por sua vez aponta de volta para condomínios; a dependência circular é resolvida permitindo que o vínculo fique vazio no momento da criação e seja preenchido logo em seguida.',
  ],
};

const implementacoesBanco = {
  paragrafos: [
    'As regras que protegem a integridade dos dados estão declaradas no próprio banco, e não apenas no código da aplicação. São de quatro tipos.',
  ],
  subsecoes: [
    { nome: 'Restrições de unicidade',
      paragrafos: [
        'Impedem duplicidade onde ela não faz sentido. Não pode existir duas cobranças da mesma unidade na mesma competência, duas unidades com o mesmo bloco e número no mesmo condomínio, nem duas marcações de leitura do mesmo comunicado pelo mesmo usuário. São também únicos, na plataforma inteira, o CPF e o e-mail de cada usuário e o CNPJ de cada condomínio.',
      ]},
    { nome: 'Verificações de valor',
      paragrafos: [
        'Recusam dado que existe mas não faz sentido. O valor de uma cobrança e de um pagamento precisa ser maior que zero; os custos de uma ordem de serviço, quando informados, não podem ser negativos; a contagem de pessoas em um espaço não pode ser negativa; a hora final de uma reserva precisa ser posterior à inicial; e o dia de vencimento escolhido pelo morador precisa estar entre 1 e 28, para existir em todos os meses do ano.',
      ]},
    { nome: 'Tipos enumerados',
      paragrafos: [
        'Situações e categorias não são texto livre: são tipos com um conjunto fechado de valores, declarados no banco. A situação de uma cobrança só pode ser uma das quatro previstas, e uma quinta simplesmente não entra. Isso evita o problema clássico de a mesma situação aparecer escrita de três formas diferentes ao longo do tempo, e faz com que qualquer valor novo exija uma migração — isto é, uma decisão consciente.',
      ]},
    { nome: 'Índices',
      paragrafos: [
        'As colunas usadas para filtrar e ordenar têm índice: situação, data, vínculo com condomínio e com unidade, placa de veículo e código de rastreio. Sem eles, a consulta precisaria varrer a tabela inteira, e o sistema ficaria mais lento à medida que o histórico crescesse — justamente quando o condomínio já dependeria dele.',
      ]},
    { nome: 'Sobre funções, gatilhos e visões',
      paragrafos: [
        'O banco do SmartCondo não usa funções armazenadas, gatilhos nem visões. A escolha é deliberada e merece ser registrada, porque é comum ver o contrário.',
        'A regra de negócio fica na aplicação por três razões. Primeira, ela passa a ser coberta pelos testes automatizados do projeto, que sobem o sistema e conferem o comportamento; regra escrita em gatilho costuma ficar fora dessa rede. Segunda, ela fica versionada junto com o restante do código, e a alteração aparece no histórico como qualquer outra. Terceira, o comportamento fica visível no lugar onde alguém vai procurá-lo: uma cobrança que muda de situação sozinha, por um gatilho, é difícil de explicar para quem está lendo o código que a criou.',
        'O que fica no banco é o que o banco faz melhor e a aplicação não consegue garantir sozinha: as restrições descritas acima. Elas valem mesmo que o dado chegue por outro caminho, e é exatamente por isso que estão lá.',
      ]},
  ],
};

module.exports = { modeloEntidadeRelacionamento, relacionamentos, implementacoesBanco };
