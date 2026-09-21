# O que mudou na documentação

Registro das alterações feitas no documento do Projeto Integrador I em
relação à versão anterior (`DocumentacaoSmartCondo` em PDF, 40 páginas).

O texto escrito pelo grupo foi **preservado**. As mudanças abaixo são de
duas naturezas: correções do que não correspondia mais ao sistema, e
seções novas descrevendo o que foi construído desde então.

## Correções

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

## Seções novas

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

> **Pendente de atualizar no .docx:** a seção 12 ainda não menciona a
> paleta de contraste. O sistema hoje tem um conjunto de cores
> semânticas com um tom por tema, cada valor escolhido para passar os
> 4,5:1 do WCAG AA sobre todos os fundos em que a cor aparece, e o modo
> alto contraste usa os mesmos tokens em versão 7:1 (AAA). A medição é
> feita por script, percorrendo as 38 páginas nos dois temas.

## Numeração

A numeração de 1 a 12 **não mudou**, de propósito: os comentários do
código-fonte citam seções da documentação (por exemplo "seção 6",
"seção 11.5.3") e continuariam válidos. As seções novas entraram como
13, 14 e 15, e apenas conclusão, cronograma e bibliografia foram
deslocadas para 16, 17 e 18 — nenhuma delas é citada no código.

## Formatação

Segue a ABNT (NBR 14724): Arial 12, entrelinhas 1,5, texto justificado,
recuo de 1,25 cm na primeira linha, margens de 3 cm (esquerda e
superior) e 2 cm (direita e inferior), papel A4 e numeração de página no
canto superior direito.

O cronograma ficou numa página em paisagem: em retrato as seis colunas
teriam 2,5 cm e palavras como "VLibras/Acessibilidade" estourariam a
célula.

## Figuras

As 25 figuras da seção 11 foram capturadas do sistema em funcionamento,
com dados reais vindos da API e do banco — não são mais protótipos do
Figma.

## Antes de entregar

1. Abra o arquivo no Word.
2. Clique com o botão direito no sumário e escolha **Atualizar campo →
   Atualizar o índice inteiro**. O Word monta o sumário com os números
   de página corretos.
3. Confira se a capa está no formato que o professor pede (algumas
   disciplinas exigem nome da instituição, curso e cidade).
