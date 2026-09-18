# Modelagem completa

Estrutura final do SmartCondo: **16 tabelas**, com financeiro, comunicados,
portaria (visitantes e encomendas), ocorrências, reservas, ocupação das
áreas em tempo real e permissões do porteiro.

É a mesma estrutura que o back-end cria pelas migrações do Alembic
(`backend/alembic/`) e a mesma carga do comando `python -m app.seed`.

Para **apresentar o início do projeto**, use a versão reduzida na pasta
acima ([`../`](../)) — 5 tabelas, mais fácil de explicar.

---

## Como executar no pgAdmin

Igual à versão reduzida: crie o banco, abra o **Query Tool**, execute
`01_criar_tabelas.sql` e depois `02_carga_dados.sql`.

Os dois são reexecutáveis.

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
`CREATE TYPE ... AS ENUM` em vez de texto livre.

**Referência circular.** `condominios.sindico_id` aponta para `usuarios` e
`usuarios.condominio_id` aponta para `condominios`. Por isso as chaves
estrangeiras são criadas depois de todas as tabelas existirem, e na carga o
condomínio entra sem síndico, com o vínculo fechado por um `UPDATE` no fim.

**Contadores.** A carga insere os `id` explicitamente e reposiciona as
sequências com `setval` ao final; sem isso, o primeiro cadastro feito pelo
sistema tentaria repetir um `id` já usado.

**Senhas.** Gravadas em hash bcrypt, nunca em texto puro.

---

## Contas carregadas

Todas com a senha `smartcondo123`:
`admin@smartcondo.com` (administrador), `sindico@smartcondo.com`,
`porteiro@smartcondo.com` e `renata@smartcondo.com` (porteiros),
`morador@smartcondo.com`, `ana@smartcondo.com`, `bruno@smartcondo.com`,
`marina@smartcondo.com` (moradores) e `pedro@smartcondo.com` (aguardando
aprovação do síndico).

Código de acesso do condomínio: `PALM-2025`.
