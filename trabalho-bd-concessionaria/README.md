# Trabalho de Banco de Dados: Concessionária de Veículos

Implementação básica do banco de dados de uma concessionária em **MySQL 8.0**,
seguindo as orientações do professor Odirley Franco (entrega em 24/09, até as 19 h).

| Arquivo | O que é |
|---|---|
| `Documentacao_Concessionaria_ABNT.docx` | **A documentação de entrega**, no padrão ABNT (NBR 14724) |
| `Documentacao_Concessionaria_ABNT.pdf` | A mesma documentação em PDF, para conferir |
| `script_concessionaria.sql` | O script completo: cria o banco e as tabelas e faz a carga (INSERT, UPDATE, DELETE) |
| `diagramas/mer.png`, `diagramas/der.png` | MER (conceitual, notação de Chen) e DER (lógico, pé de galinha) |
| `fontes/` | Os scripts que geram os diagramas e o `.docx`, e a saída real da execução no MySQL |

A **apresentação** foi publicada como deck em
<https://claude.ai/artifact/W3iH8CZToEwpJy1QJDPsxA> (19 slides com notas do
apresentador; dá para baixar em PowerPoint ou PDF pelo próprio deck).

## O que o professor pediu e onde está

| Pedido | Onde está na documentação |
|---|---|
| Introdução e objetivo | Seções 1 e 2 |
| Escolha do banco de dados (1ª etapa: definir o SGBD) | Seção 3, com o Quadro 1 comparando MySQL, PostgreSQL e SQL Server |
| MER | Seção 4.2, Figura 1 |
| DER | Seção 4.3, Figura 2 |
| Dicionário de dados | Seção 4.4, Quadros 5 a 9 |
| Explicação da implementação: criar o database (2ª etapa) | Seção 5.1 |
| Criar a estrutura de tabelas (3ª etapa) | Seção 5.2 |
| Carga de dados com INSERT, UPDATE e DELETE (4ª etapa) | Seção 5.3, com o estado das tabelas antes e depois |
| Comandos utilizados | Seção 5 inteira, Quadro 19 (resumo) e Apêndice A (script completo) |
| Conclusão e referências | Seção 6 e Referências |

## Antes de entregar: preencher os campos em amarelo

A capa, a folha de rosto e o primeiro slide têm campos que só o grupo sabe:

- `[NOME DA INSTITUIÇÃO]`, `[NOME DO CURSO]`, `[NOME DA DISCIPLINA]` e `[CIDADE]`;
- `[NOME COMPLETO DO INTEGRANTE 1]` a `4` (se o grupo tiver menos de 4, apague as linhas que sobrarem).

No `.docx` eles estão com **fundo amarelo**. Depois de preencher, selecione o
texto e tire o realce. Trocar esses campos não muda a paginação.

O sumário e as listas de figuras, quadros e códigos já vêm com os números de
página preenchidos. Se o grupo mudar o texto a ponto de empurrar páginas,
confira os números antes de entregar.

## O que mudou em relação ao que o grupo já tinha

O modelo do grupo foi mantido: as mesmas 5 tabelas, colunas, tipos e chaves, e
todos os registros originais continuam no script, com os mesmos ids. O que foi
acrescentado:

1. **Script reexecutável**: `DROP DATABASE IF EXISTS` no início e `SET NAMES utf8mb4`
   para os acentos. Antes, rodar o script uma segunda vez dava erro de tabela já existente.
2. **Restrições CHECK**: situação do veículo só pode ser `Disponivel`, `Reservado` ou
   `Vendido`; preço, salário e valor da venda precisam ser maiores que zero.
3. **Restrições com nome** (`fk_venda_cliente`, `uq_venda_veiculo`...), o que deixa as
   mensagens de erro do MySQL legíveis.
4. **Mais dados de exemplo**: 3 fornecedores, 7 veículos (um 0 km sem placa, para mostrar
   o NULL), 4 clientes, 3 funcionários e 3 vendas.
5. **Vendas em transação**: cada venda faz o INSERT em `vendas` e o UPDATE da situação do
   veículo entre `START TRANSACTION` e `COMMIT`.
6. **Testes de integridade** (comentados no script): excluir cliente com venda, vender o
   mesmo veículo duas vezes e gravar uma situação inválida. Os três são recusados pelo MySQL.
7. **Consultas de verificação** novas: contagem por tabela, estoque com `LEFT JOIN` e
   total vendido por funcionário com `GROUP BY`.

## Como rodar o script

**MySQL Workbench:** abra `script_concessionaria.sql` e execute tudo (Ctrl+Shift+Enter).

**Terminal:**

```bash
mysql -u root -p < script_concessionaria.sql
```

O script foi executado de ponta a ponta no MySQL 8.0.46. A saída completa, com
cada `Query OK` e o resultado das consultas, está em `fontes/saida_execucao.txt`.

## Regerando a documentação

Só é preciso se o grupo quiser mudar o conteúdo pelos scripts em vez de editar o `.docx` direto.

```bash
cd fontes
npm install                    # instala a biblioteca docx
python diagramas.py            # gera ../diagramas/*.svg
node render.js                 # converte os SVGs em PNG (precisa do Playwright)
python coletar_resultados.py   # roda o script num MySQL local e grava resultados.json
python paginar.py              # gera o .docx e o .pdf com o sumário paginado (precisa do LibreOffice)
```

| Arquivo em `fontes/` | O que tem |
|---|---|
| `conteudo.js` | Todo o texto do documento: capa, resumo, seções, quadros e referências |
| `montar.js` | A formatação ABNT: margens, fontes, títulos, quadros, códigos e paginação |
| `paginar.py` | Converte para PDF, acha a página de cada título e preenche o sumário e as listas |
| `coletar_resultados.py` | Executa o script no MySQL e guarda as saídas mostradas no documento |
| `diagramas.py`, `render.js` | Desenham o MER e o DER |
