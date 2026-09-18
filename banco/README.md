# Banco de dados — SmartCondo

Scripts SQL do banco, prontos para rodar no **pgAdmin**.

| Arquivo | O que faz |
|---|---|
| `01_criar_tabelas.sql` | Cria os tipos, as 16 tabelas, as chaves e os índices |
| `02_carga_dados.sql` | Carrega um condomínio completo de demonstração |

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

## As 16 tabelas

| Tabela | Guarda |
|---|---|
| `condominios` | Condomínios cadastrados pelo administrador |
| `unidades` | Apartamentos ou casas de cada condomínio |
| `usuarios` | Administradores, síndicos, porteiros e moradores |
| `permissoes_porteiro` | O que cada porteiro pode fazer, definido pelo síndico |
| `codigos_verificacao` | Códigos de confirmação e de recuperação de senha |
| `espacos_comuns` | Salão, churrasqueira, piscina, academia e demais áreas |
| `reservas` | Pedidos de reserva, aprovados ou recusados pelo síndico |
| `registros_ocupacao` | Contagem de pessoas nas áreas de uso livre |
| `preferencias_cobranca` | Dia do vencimento e forma de pagamento do morador |
| `cobrancas` | Taxa condominial por unidade e competência |
| `pagamentos` | Pagamentos recebidos, com meio, valor e data |
| `comunicados` | Avisos publicados pelo síndico |
| `leituras_comunicado` | Quem já leu cada comunicado |
| `visitantes` | Registro de visitantes, com a foto do vídeo porteiro |
| `encomendas` | Encomendas recebidas na portaria |
| `ocorrencias` | Chamados abertos por moradores, porteiros ou síndico |

---

## Detalhes da modelagem

**Tipos enumerados.** Papel, status, forma de pagamento e categoria usam
`CREATE TYPE ... AS ENUM`, e não texto livre: o banco recusa qualquer valor
fora da lista.

**Referência circular.** `condominios.sindico_id` aponta para `usuarios` e
`usuarios.condominio_id` aponta para `condominios` — uma tabela referencia a
outra. Por isso:

- em `01_criar_tabelas.sql`, as chaves estrangeiras são criadas **depois**
  de todas as tabelas existirem (seção 4);
- em `02_carga_dados.sql`, o condomínio entra **sem** o síndico, e o vínculo
  é fechado por um `UPDATE` no fim (seção 3).

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
