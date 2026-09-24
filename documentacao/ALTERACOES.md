# O que mudou na documentação

Registro das alterações feitas no documento do Projeto Integrador I em
relação à versão anterior (`DocumentacaoSmartCondo` em PDF, 40 páginas).

O texto escrito pelo grupo foi **preservado**. As mudanças abaixo são de
duas naturezas: correções do que não correspondia mais ao sistema, e
seções novas descrevendo o que foi construído desde então.

## Versão 2.4 — documentos do condomínio com arquivo de verdade

| Seção | O que mudou |
|---|---|
| 9 Requisitos funcionais | RF032: o síndico envia o arquivo (PDF ou imagem), em vez de digitar um endereço, e o arquivo só abre com o token de quem tem direito |
| 10 Requisitos não funcionais | RNF017 passa a cobrir os documentos do condomínio |
| 11.6.5 Tela de documentos | O texto cita a tela do síndico que publica e a abertura com o token |
| 14 a 17 | Em documentos, arquivo_url dá lugar a arquivo e tipo_conteudo — agora 235 atributos |
| 20 Arquitetura | Os documentos do condomínio também ficam sem endereço público |
| 21 API REST | 99 endpoints |
| 23 Testes | 314 casos no servidor e 58 testes de interface |

**Por que mudou.** O documento era só um endereço digitado pelo síndico:
os de demonstração apontavam para um servidor que não existe, e nada
impedia um endereço `javascript:`, que rodaria na tela do morador ao ser
clicado. Agora o arquivo é enviado, conferido pelo conteúdo e guardado
fora do alcance público.

**Planilhas exportadas.** As listas de moradores e de cobranças exportadas
em CSV escreviam o texto como veio; um nome cadastrado como
`=HYPERLINK(...)` virava fórmula ao abrir no Excel. Agora esse texto ganha
um apóstrofo na frente, e os valores saem com vírgula decimal.

## Versão 2.3 — revisão geral

| Seção | O que mudou |
|---|---|
| 9 Requisitos funcionais | RF016 e RF034: faixas de data aceitas na reserva e na cobrança. RF006: o morador recebe e-mail com a decisão do síndico. RF027: a lista de placas do pátio é da portaria e do síndico. RF028: a ocorrência aceita foto |
| 10 Requisitos não funcionais | RNF017 passa a cobrir as fotos das ocorrências |
| 13.3 Tela de cadastro morador | O texto deixa de citar vagas de garagem e passa a citar os documentos; figura refeita com o formulário novo |
| 17 Dicionário de dados | Em ocorrencias, foto_url dá lugar a foto_arquivo |
| 20 Arquitetura | Limite de envio de códigos; as permissões do porteiro valem também para consultar |
| 21 API REST | 98 endpoints |
| 23 Testes | 305 casos no servidor e 56 testes de interface |

**Formulários mais enxutos.** Os cadastros pediam dados que o sistema
nunca guardava: no do morador, nome social, número do RG, estado civil,
gênero, profissão, contato de emergência, andar, data de mudança,
veículos e dependentes; no do porteiro, RG, endereço, turno, contrato,
NIS/PIS, CTPS e até a certidão de antecedentes criminais, em anexo
obrigatório. Saíram todos: a LGPD manda coletar só o necessário, e o que
comprova o vínculo do morador são os documentos, que o síndico confere.

## Versão 2.2 — fotos da portaria e documentos do cadastro

| Seção | O que mudou |
|---|---|
| 9 Requisitos funcionais | RF021 e RF024 passam a citar a foto do visitante e do volume. Dois novos: RF043 enviar documentos no cadastro e RF044 conferir documentos antes de aprovar |
| 10 Requisitos não funcionais | RNF016 ganha o prazo de guarda das fotos e o descarte dos documentos na recusa e na inativação; RNF017 passa a cobrir o acesso restrito aos arquivos |
| 14 a 17 | A tabela documentos_cadastro entra no modelo, no diagrama, nos relacionamentos e no dicionário — agora 21 entidades, 234 atributos e 44 relacionamentos. Em visitantes e encomendas, foto_url dá lugar a foto_arquivo |
| 20 Arquitetura | Armazenamento das fotos da portaria e dos documentos sem endereço público, e a autorização de envio devolvida pelo cadastro |
| 21 API REST | 96 endpoints em treze módulos |
| 23 Testes | 282 casos no servidor e 54 testes de interface, incluindo os fluxos com arquivo de ponta a ponta, a câmera e a logo |

## Versão 2.1 — foto de perfil, chat, SMS e testes de interface

| Seção | O que mudou |
|---|---|
| 9 Requisitos funcionais | Quatro novos: RF039 foto de perfil, RF040 chat, RF041 ligação, RF042 código por SMS. O RF005 passa a citar a escolha do canal |
| 10 Requisitos não funcionais | Novo RNF017, arquivos conferidos pelo conteúdo. Os requisitos de padrões passam a RNF018 a RNF021 |
| 11 Diagrama de caso de uso | Dois casos novos: conversar pelo chat e enviar foto de perfil |
| 14 a 17 | A tabela de mensagens entra no modelo, no diagrama, nos relacionamentos e no dicionário — agora 20 entidades, 227 atributos e 43 relacionamentos |
| 20 Arquitetura | Envio por SMS, armazenamento das fotos e funcionamento do chat |
| 21 API REST | 88 endpoints em treze módulos, com mensagens e arquivos |
| 23 Testes | 249 casos no servidor, 47 testes de interface num navegador real e a comparação dos scripts SQL com as migrações |

**Sumário.** O arquivo agora pede ao Word que atualize os campos ao ser
aberto: o Word pergunta se deve atualizar, e basta responder "Sim" para
o sumário aparecer com os números de página.

## Versão 2.0 — a estrutura do modelo do professor

O professor entregou um modelo de documentação como referência. Comparado
a ele, o documento tinha texto suficiente nas seções de negócio, mas
faltavam as seções técnicas que o modelo traz: requisitos numerados,
diagrama de casos de uso, modelagem e dicionário de dados. Esta versão
acrescenta essas seções e reorganiza a ordem para acompanhar o modelo.
O documento passou de cerca de 5.800 para cerca de 15.800 palavras, 89
tabelas e 30 figuras.

| Seção | O que entrou |
|---|---|
| Histórico de revisões | Tabela logo depois da capa, como no modelo: data, versão, descrição e autores |
| 7 Identificação dos requisitos | Reescrita: explica os identificadores RF e RNF e os três níveis de prioridade |
| 9 Requisitos funcionais | **38 requisitos** (RF001 a RF038), cada um com atores, prioridade, descrição, entradas e pré-condições, saídas e pós-condições. Cada um corresponde a algo já implementado e testado |
| 10 Requisitos não funcionais | **20 requisitos** (RNF001 a RNF020) em cinco grupos — usabilidade, confiabilidade, desempenho, segurança e padrões —, cada um com a forma como é verificado |
| 11 Diagrama de caso de uso | Diagrama UML com os 4 atores e 25 casos de uso |
| 12 Casos de uso | Os casos de uso que antes ficavam na seção 9, agora cada um com subseção própria (12.1 a 12.5) |
| 14 Modelo entidade-relacionamento | As decisões de modelagem e o quadro das 19 entidades |
| 15 Diagrama entidade-relacionamento | Quatro figuras: visão de conjunto e três recortes por assunto com todos os atributos |
| 16 Relacionamentos | As 40 chaves estrangeiras, cada uma com o seu significado |
| 17 Dicionário de dados | As 19 tabelas e os 220 atributos: tipo, obrigatoriedade, chave e descrição |
| 18 Implementações no banco | Restrições de unicidade, verificações de valor, tipos enumerados, índices, e por que o projeto não usa gatilhos nem visões |

**O que é gerado do banco.** O diagrama entidade-relacionamento e o
dicionário de dados não foram escritos à mão: tipos, obrigatoriedade,
chaves e valores dos tipos enumerados são lidos do PostgreSQL em
funcionamento pelos scripts de `fontes/diagramas/`. As descrições em
português ficam no próprio script, e a geração falha se alguma coluna ou
chave estrangeira ficar sem descrição — assim o dicionário não envelhece
em silêncio quando o banco muda.

**Capa.** Saíram Ian Araujo Ramos Jares e João Victor Arantes Oliveira,
que não fazem mais parte do grupo, e entrou Lenini Bellodi Júnior, que
faz e não aparecia; com isso o gestor do projeto, na
seção 2, passou a ser Júlio Zadi. O ano da capa continua 2025, que é
quando o projeto começou.

## Versão 1.x

Os números de seção citados nesta parte são os da **numeração antiga**,
anterior à versão 2.0.

### Correções

| Onde | O que estava | O que passou a estar |
|---|---|---|
| Todo o documento | Três perfis de acesso | Quatro perfis — entrou o **administrador**, que cadastra os condomínios e cria a conta do síndico |
| 8 Descrição dos usuários | Síndico, porteiro e morador | Acrescentado o administrador, com a descrição do que ele faz |
| 9 Caso de uso "Cadastro" | "O usuário clica no botão para escolher quem irá cadastrar" | Reescrito para a hierarquia real: o administrador cria o síndico, o síndico cria porteiro e morador, e o morador também pode se cadastrar sozinho com o código do condomínio, ficando pendente de aprovação |
| 9 Caso de uso "Cadastro do condomínio" | Aparecia **duas vezes**, idêntico, e com o síndico como usuário principal | Aparece uma vez, com o administrador como usuário principal, e explica o código de acesso gerado |
| 10.5 Node.js | Listado como tecnologia do back-end | Removido. O back-end é FastAPI puro; não há Node.js no projeto |
| 10 Linguagens | Seis itens | Acrescentados FastAPI (10.6) e SQLAlchemy/Alembic (10.7), que são o que de fato foi usado |
| 13 Conclusão | "Python e Node.js (para o back-end e funcionalidades em tempo real como o vídeo porteiro)" | "Python com FastAPI no back-end". Acrescentado um parágrafo com o estado atual do sistema |
| Sumário | Números de página todos "2" e "3"; três itens numerados "10.5"; "11.4 Mudança de cores" (deveria ser 12.4); "14" indicado como bibliografia quando é o cronograma | Sumário automático do Word, que numera as páginas e os itens sozinho ao ser atualizado |
| 11.2 | O sumário dizia "Tela de cadastro do síndico" e o corpo mostrava o porteiro | Corrigido para "Tela de cadastro do porteiro", que é o que a seção descreve |

### Seções novas

- **11.4 Tela de login** — preenche a lacuna do 11.4, que existia no
  sumário mas não no corpo.
- **11.5.5 a 11.5.7** — telas de financeiro, manutenção e ocorrências do
  síndico.
- **11.6.5 a 11.6.7** — documentos, ocorrências e perfil do morador.
- **11.7.4** — controle de veículos do porteiro.
- **11.8 Telas do Administrador** — as três telas do painel novo.
- **13 Arquitetura e banco de dados** — as três camadas do sistema, a
  modelagem com as 19 tabelas e a seção de segurança dos dados.
- **14 API REST** — os 78 endpoints e o que cada módulo faz.
- **15 Testes automatizados** — os 196 casos de teste e o que eles cobrem.
- **12.1 Boas práticas** ganhou um parágrafo sobre o que foi de fato
  implementado em acessibilidade (rótulos associados, área mínima de
  toque, verificação em 360 px).
- **12.1 Boas práticas** ganhou mais dois parágrafos sobre o contraste:
  as cores semânticas com um valor por tema, escolhidas até alcançar
  4,5:1 sobre todos os fundos em que a cor aparece, o modo alto
  contraste em 7:1, e a medição por script, que achou 305 textos em
  desacordo e hoje não acha nenhum.
- **13.2 Segurança dos dados** ganhou três parágrafos: o bloqueio da
  conta após cinco senhas erradas, o registro de autoria de cada
  decisão do sistema, e os dois documentos legais com a base na LGPD.
- **15 Testes** passou de 196 para 216 casos, com a tabela por arquivo
  corrigida, e ganhou um parágrafo sobre as verificações automáticas a
  cada envio de código.
- **13 Arquitetura** ganhou um parágrafo sobre o envio das mensagens: os
  códigos saem por SMTP, e sem essa configuração o cadastro do morador
  travaria, porque o código não chegaria a ninguém.
- **13.2 Segurança** ganhou mais três parágrafos: o limite de tentativas
  do código de seis dígitos e por que ele existe, os cabeçalhos de
  segurança das respostas, e a verificação das permissões do porteiro em
  toda gravação.
- **Números corrigidos:** a conclusão ainda dizia 78 endpoints e 196
  casos de teste, defasada até em relação à revisão anterior. Agora são
  79 e 216, conferidos contra a coleta do pytest e o OpenAPI.

## Numeração

Na versão 1.x a numeração de 1 a 12 foi mantida de propósito, porque os
comentários do código-fonte citam seções da documentação. Na versão 2.0
ela **mudou**, para acompanhar o modelo do professor — e as citações no
código foram atualizadas no mesmo envio, para que nenhuma aponte para o
lugar errado:

| Assunto | Antes | Agora |
|---|---|---|
| Casos de uso | 9 | 12 |
| Linguagens e ferramentas | 10 | 19 |
| Prototipação das telas | 11 | 13 |
| Acessibilidade | 12 | 22 |
| Arquitetura | 13 | 20 |
| API REST | 14 | 21 |
| Testes automatizados | 15 | 23 |
| Conclusão, cronograma e bibliografia | 16 a 18 | 24 a 26 |

As seções 1 a 8 não mudaram. A modelagem do banco, que era a subseção
13.1, virou as seções 14 a 18.

## Formatação

Segue a ABNT (NBR 14724): Arial 12, entrelinhas 1,5, texto justificado,
recuo de 1,25 cm na primeira linha, margens de 3 cm (esquerda e
superior) e 2 cm (direita e inferior), papel A4 e numeração de página no
canto superior direito.

O cronograma ficou numa página em paisagem: em retrato as seis colunas
teriam 2,5 cm e palavras como "VLibras/Acessibilidade" estourariam a
célula.

## Figuras

As 25 figuras da seção 13 foram capturadas do sistema em funcionamento,
com dados reais vindos da API e do banco — não são mais protótipos do
Figma. As 5 figuras novas — o diagrama de casos de uso e os quatro do
diagrama entidade-relacionamento — são geradas por script, a partir do
banco, e podem ser refeitas a qualquer momento.

## Antes de entregar

1. Abra o arquivo no Word.
2. Clique com o botão direito no sumário e escolha **Atualizar campo →
   Atualizar o índice inteiro**. O Word monta o sumário com os números
   de página corretos.
3. Confira se a capa está no formato que o professor pede (algumas
   disciplinas exigem nome da instituição, curso e cidade).
