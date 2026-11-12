# Banco de dados — SmartCondo

Scripts SQL do banco, prontos para rodar no **pgAdmin**.

| Arquivo | O que faz |
|---|---|
| `01_criar_tabelas.sql` | Cria os tipos, as 40 tabelas, as chaves e os índices |
| `02_carga_dados.sql` | Carrega um condomínio completo de demonstração |
| `03_consultas.sql` | 14 consultas sobre os dados: junções, agrupamentos, subconsultas, janelas |
| `04_programacao.sql` | Visões, funções, procedimentos, gatilhos e um índice parcial |
| `05_seguranca.sql` | Papéis de acesso (síndico, portaria, conselho fiscal) e as permissões de cada um |
| `06_demonstracao.sql` | Usa tudo o que o 04 e o 05 criaram, dentro de uma transação desfeita no fim |

Os dois arquivos são SQL puro, sem comentários — as explicações ficam
neste README.

Banco: **PostgreSQL 16**.

---

## Como executar no pgAdmin

1. **Crie o banco.** No painel da esquerda, clique com o botão direito em
   **Databases → Create → Database…** e dê o nome `smartcondo`.

2. **Selecione o banco** `smartcondo` que acabou de criar.

3. **Abra o Query Tool** em **Tools → Query Tool**.

4. **Abra `01_criar_tabelas.sql`** pelo ícone de pasta e execute com **F5**.
   Vão aparecer avisos `NOTICE: table ... does not exist, skipping` na
   primeira execução — é esperado: o script apaga o que existir antes de
   recriar, e na primeira vez não existe nada.

5. **Abra `02_carga_dados.sql`** e execute com **F5**.

Os dois scripts podem ser executados quantas vezes quiser: cada um limpa
o que criou antes de recriar.

---

## Conferindo

Depois do passo 4, as tabelas criadas:

```sql
SELECT tablename FROM pg_tables
 WHERE schemaname = 'public'
 ORDER BY tablename;
```

Depois do passo 5, os dados carregados:

```sql
SELECT 'condominios' AS tabela, COUNT(*) FROM condominios
UNION ALL SELECT 'unidades',    COUNT(*) FROM unidades
UNION ALL SELECT 'usuarios',    COUNT(*) FROM usuarios
UNION ALL SELECT 'espacos',     COUNT(*) FROM espacos_comuns
UNION ALL SELECT 'reservas',    COUNT(*) FROM reservas
UNION ALL SELECT 'cobrancas',   COUNT(*) FROM cobrancas
UNION ALL SELECT 'pagamentos',  COUNT(*) FROM pagamentos
UNION ALL SELECT 'comunicados', COUNT(*) FROM comunicados;
```

---

## 2ª parte: consultas, visões, funções, gatilhos e permissões

Depois do `02`, execute na ordem, do mesmo jeito (abrir o arquivo e **F5**):

6. **`03_consultas.sql`** — só lê os dados. Com o arquivo inteiro, o
   pgAdmin mostra o resultado da última consulta; para ver outra,
   selecione só ela e aperte **F5**.
7. **`04_programacao.sql`** — cria a tabela `log_cobrancas`, o índice
   `ix_cobrancas_em_aberto`, as visões `vw_*`, as funções `fn_*`, os
   procedimentos `sp_*` e os gatilhos `trg_*`.
8. **`05_seguranca.sql`** — conectado como **`postgres`**, porque cria
   papéis (`CREATE ROLE`). Termina mostrando o que cada papel pode fazer.
9. **`06_demonstracao.sql`** — também como **`postgres`**. Começa com
   `BEGIN` e termina com `ROLLBACK`: gera a taxa do mês, registra um
   pagamento e tenta cinco operações proibidas, e no fim nada disso fica
   no banco. As tentativas barradas aparecem na aba **Messages**.

Todos podem ser executados de novo. Se o `01` for executado outra vez,
execute também o `04` e o `05`: o `01` recria as tabelas e leva junto as
visões, os gatilhos e as permissões.

| Objeto | Para quê |
|---|---|
| `vw_situacao_unidades` | Cada apartamento: responsável, cobranças e valor em atraso, a vencer, em dia ou inadimplente |
| `vw_balancete_mensal` | Receitas, despesas, saldo do mês e saldo acumulado |
| `vw_moradores` | Moradores sem CPF, telefone nem senha, e com o e-mail mascarado |
| `fn_total_pago(cobranca)` | Quanto já foi abatido da cobrança |
| `fn_encargos(cobranca, dia)` | Multa (2%) e juros (1% ao mês, dia a dia) do atraso, como o sistema calcula |
| `fn_rateio(condominio, total)` | Divide um total pela fração ideal, sem perder centavo |
| `sp_gerar_taxa_mensal(...)` | Lança a taxa do mês para todos os apartamentos, pelo mesmo valor ou pela fração |
| `sp_registrar_pagamento(...)` | Registra o pagamento com a multa e os juros do dia |
| `trg_valida_pagamento` | Barra pagamento de cobrança cancelada ou negociada, e pagamento acima do que falta |
| `trg_quita_cobranca` | Marca a cobrança como paga quando o que foi pago cobre o valor |
| `trg_log_cobranca` | Guarda em `log_cobrancas` toda mudança de situação, valor ou vencimento |
| `trg_atualizado_em` | Atualiza a data de alteração em cobranças, unidades e reservas |
| `ix_cobrancas_em_aberto` | Índice parcial: só as cobranças abertas ou vencidas, que são as consultadas no dia a dia |

| Papel | Pode |
|---|---|
| `smartcondo_sindico` | Ler, incluir e alterar tudo, menos o histórico e o log; não apaga nada |
| `smartcondo_portaria` | Visitantes, encomendas e veículos; dos moradores, só nome e apartamento — sem CPF e sem financeiro |
| `smartcondo_conselho` | Só as visões de situação das unidades e do balancete |

Esses objetos são da demonstração do banco: o sistema (back-end) não
depende deles e faz as mesmas regras no próprio código.

---

## As 40 tabelas

| Tabela | Guarda |
|---|---|
| `condominios` | Condomínios cadastrados pelo administrador |
| `unidades` | Apartamentos ou casas de cada condomínio, com as vagas e a fração ideal |
| `usuarios` | Administradores, síndicos, porteiros e moradores; quem tem mais de um papel ou apartamento tem um perfil por papel, ligado ao cadastro com o login |
| `permissoes_porteiro` | O que cada porteiro pode fazer, definido pelo síndico |
| `codigos_verificacao` | Códigos de confirmação e de recuperação de senha |
| `espacos_comuns` | Salão, churrasqueira, piscina, academia e demais áreas |
| `reservas` | Pedidos de reserva, aprovados ou recusados pelo síndico |
| `registros_ocupacao` | Contagem de pessoas nas áreas de uso livre |
| `preferencias_cobranca` | Dia do vencimento e forma de pagamento do morador |
| `cobrancas` | Taxa condominial por unidade e competência, cotas extras, multas, uso de espaço e parcelas de acordo |
| `acordos` | Acordos de parcelamento: as cobranças vencidas de um apartamento divididas em parcelas |
| `pagamentos` | Pagamentos recebidos, com meio, valor e data |
| `despesas` | O que o condomínio gastou, com o comprovante: a prestação de contas |
| `assembleias` | Assembleias virtuais: convocação, período de votação e cancelamento |
| `itens_pauta` | Itens da pauta de cada assembleia, com a maioria que exigem |
| `votos` | Um voto por apartamento em cada item da pauta |
| `comunicados` | Avisos publicados pelo síndico |
| `leituras_comunicado` | Quem já leu cada comunicado |
| `visitantes` | Registro de visitantes, com a foto do vídeo porteiro |
| `autorizacoes_visita` | Entradas liberadas pelo morador com antecedência (diarista, prestador, convidados) |
| `encomendas` | Encomendas recebidas na portaria, com a foto do volume |
| `ocorrencias` | Chamados abertos por moradores, porteiros ou síndico |
| `movimentacoes_veiculo` | Entradas e saídas do estacionamento |
| `veiculos_unidade` | Placas cadastradas por apartamento, para a portaria reconhecer o carro |
| `mudancas` | Mudanças pedidas pelo morador e aprovadas ou recusadas pelo síndico |
| `horarios_mudanca` | Dias e horários de mudança do regimento de cada condomínio |
| `reformas` | Obras comunicadas pelo morador (NBR 16280), com o responsável técnico e a avaliação do síndico |
| `infracoes` | Advertências e multas do síndico, com a defesa do morador e a decisão |
| `anotacoes_portaria` | O livro da portaria: a passagem de turno da equipe; não se apaga nem se edita |
| `ciencias_anotacao` | Quem leu cada anotação importante do livro, e quando |
| `declaracoes_quitacao` | Declarações de que o apartamento está em dia, com o código que qualquer um confere |
| `planos_manutencao` | O que vence de tempos em tempos (AVCB, extintores, caixa d'água), com o próximo vencimento |
| `realizacoes_manutencao` | Cada vez que uma manutenção preventiva foi feita, com o custo |
| `chaves` | O quadro de chaves da portaria: áreas comuns e apartamentos |
| `movimentacoes_chave` | Quem levou cada chave, quem entregou e quem recebeu de volta |
| `ordens_servico` | Manutenção aberta e acompanhada pelo síndico |
| `documentos` | Atas, convenção, regimento e plantas |
| `documentos_cadastro` | RG, comprovante de residência e escritura enviados no cadastro do morador |
| `mensagens` | Conversas do chat entre síndico, porteiros e moradores |
| `registros_alteracao` | Quem criou, editou, inativou ou reativou cada registro, e quando |

---

## Detalhes da modelagem

**Tipos enumerados.** Papel, status, forma de pagamento e categoria usam
`CREATE TYPE ... AS ENUM`, e não texto livre: o banco recusa qualquer valor
fora da lista.

**Referência circular.** `condominios.sindico_id` aponta para `usuarios` e
`usuarios.condominio_id` aponta para `condominios` — uma tabela referencia a
outra. Por isso:

- em `01_criar_tabelas.sql`, as chaves estrangeiras são criadas **depois**
  de todas as tabelas existirem;
- em `02_carga_dados.sql`, o condomínio entra **sem** o síndico, e o vínculo
  é fechado por um `UPDATE` no fim do script.

**Contadores.** A carga insere os `id` explicitamente, então as sequências
são reposicionadas com `setval` no fim do script. Sem isso, o primeiro
cadastro feito pelo sistema tentaria repetir um `id` já usado.

**Senhas.** Gravadas em hash **bcrypt**, nunca em texto puro — nem no banco,
nem no script de carga. O mesmo vale para os códigos de verificação.

---

## Contas carregadas

Todas com a senha `smartcondo123`:

| E-mail | Papel |
|---|---|
| `admin@smartcondo.com` | Administrador da plataforma |
| `sindico@smartcondo.com` | Síndico |
| `porteiro@smartcondo.com` | Porteiro — todas as permissões |
| `renata@smartcondo.com` | Porteira — sem veículos nem ocorrências |
| `morador@smartcondo.com` | Morador do apto 204 |
| `ana@smartcondo.com` | Moradora do apto 301 |
| `bruno@smartcondo.com` | Morador do apto 102 |
| `marina@smartcondo.com` | Moradora do apto 410 |
| `pedro@smartcondo.com` | Aguardando aprovação do síndico |

**Código de acesso do condomínio:** `PALM-2025` — é o que o morador informa
para se cadastrar sozinho.

---

## Relação com a aplicação

Estes scripts são a mesma estrutura que o back-end cria pelas migrações do
Alembic (`backend/alembic/`) e a mesma carga do comando
`python -m app.seed`. Foram gerados a partir do banco real, então não
divergem da aplicação.

Quem for rodar a API pode usar as migrações; quem quiser apenas ver o banco
no pgAdmin usa estes dois arquivos.
