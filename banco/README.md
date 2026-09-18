# Banco de dados — SmartCondo

Scripts SQL para rodar no **pgAdmin** (PostgreSQL).

| Arquivo | O que faz |
|---|---|
| `01_criar_tabelas.sql` | Cria as 5 tabelas, as chaves e as restrições |
| `02_carga_dados.sql` | Carrega 18 registros de exemplo |

Esta é a **versão reduzida**, para apresentar o início do projeto. A
modelagem completa do sistema, com 16 tabelas, está em
[`completo/`](completo/).

Os arquivos são SQL puro, sem comentários — as explicações ficam aqui.

---

## Como executar no pgAdmin

1. **Crie o banco.** Botão direito em **Databases → Create → Database…**,
   com o nome `smartcondo`.
2. **Selecione** o banco `smartcondo`.
3. **Tools → Query Tool**.
4. Abra `01_criar_tabelas.sql` (ícone de pasta) e execute com **F5**.
   Na primeira vez aparecem avisos `NOTICE: table ... does not exist,
   skipping` — é esperado, o script apaga antes de recriar.
5. Abra `02_carga_dados.sql` e execute com **F5**.

Os dois podem ser executados quantas vezes quiser.

---

## As 5 tabelas

| Tabela | Guarda | Registros |
|---|---|---|
| `condominios` | O condomínio | 1 |
| `unidades` | Apartamentos do condomínio | 4 |
| `usuarios` | Síndico, porteiro e moradores | 5 |
| `espacos_comuns` | Salão, churrasqueira, piscina, academia | 4 |
| `reservas` | Reservas dos espaços pelos moradores | 4 |

### Relacionamentos

```
condominios
    ├── unidades          (um condomínio tem várias unidades)
    ├── usuarios          (um condomínio tem vários usuários)
    └── espacos_comuns    (um condomínio tem vários espaços)

usuarios ──── unidades    (o morador pertence a uma unidade)

reservas ──── usuarios          (quem reservou)
         └──── espacos_comuns   (o que foi reservado)
```

---

## Regras garantidas pelo banco

Não são validações só da tela — o banco recusa o dado errado:

| Regra | Como |
|---|---|
| `papel` só aceita síndico, porteiro ou morador | `CHECK` |
| Morador precisa ter unidade; síndico e porteiro, não | `CHECK` |
| `status` da reserva só aceita pendente, aprovada ou recusada | `CHECK` |
| A hora de término é depois da de início | `CHECK` |
| Capacidade do espaço é maior que zero | `CHECK` |
| E-mail e CNPJ não se repetem | `UNIQUE` |
| Não há duas unidades com o mesmo número no condomínio | `UNIQUE` |
| Toda unidade, usuário, espaço e reserva aponta para algo que existe | `FOREIGN KEY` |

---

## Conferindo

Tabelas criadas:

```sql
SELECT tablename FROM pg_tables
 WHERE schemaname = 'public'
 ORDER BY tablename;
```

Dados carregados:

```sql
SELECT 'condominios' AS tabela, COUNT(*) FROM condominios
UNION ALL SELECT 'unidades',    COUNT(*) FROM unidades
UNION ALL SELECT 'usuarios',    COUNT(*) FROM usuarios
UNION ALL SELECT 'espacos',     COUNT(*) FROM espacos_comuns
UNION ALL SELECT 'reservas',    COUNT(*) FROM reservas;
```

Uma consulta que atravessa as cinco tabelas, boa para mostrar na
apresentação:

```sql
SELECT u.nome AS morador,
       un.bloco || '-' || un.numero AS unidade,
       e.nome AS espaco,
       r.data, r.hora_inicio, r.hora_fim, r.status
  FROM reservas r
  JOIN usuarios u       ON u.id  = r.morador_id
  JOIN unidades un      ON un.id = u.unidade_id
  JOIN espacos_comuns e ON e.id  = r.espaco_id
 ORDER BY r.data;
```

---

## Contas carregadas

Todas com a senha `smartcondo123`:

| E-mail | Papel | Unidade |
|---|---|---|
| `sindico@smartcondo.com` | Síndico | — |
| `porteiro@smartcondo.com` | Porteiro | — |
| `joao@smartcondo.com` | Morador | B-204 |
| `ana@smartcondo.com` | Morador | B-301 |
| `bruno@smartcondo.com` | Morador | A-102 |

As senhas estão em **hash bcrypt**, nunca em texto puro.

---

## Versão completa

A pasta [`completo/`](completo/) tem a modelagem final do sistema: 16
tabelas, cobrindo também financeiro, comunicados, portaria (visitantes e
encomendas), ocorrências e permissões do porteiro. É a estrutura que o
back-end usa de verdade (`backend/alembic/`).

Use a versão reduzida para apresentar; a completa fica como referência do
que o projeto alcança.
