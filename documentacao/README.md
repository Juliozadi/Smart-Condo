# Documentação — SmartCondo

| Arquivo | O que é |
|---|---|
| `DocumentacaoSmartCondo.docx` | **O documento de entrega.** Projeto Integrador I, formatado pela ABNT (NBR 14724) |
| `ALTERACOES.md` | O que mudou em relação à versão anterior, item por item |
| `fontes/` | Os scripts que geram o `.docx` |

## Antes de entregar

Abra o `.docx` no Word e **atualize o sumário**: botão direito sobre ele →
*Atualizar campo* → *Atualizar o índice inteiro*. Os números de página só
são calculados nessa hora.

## Regerando o documento

O documento é gerado por script, para que uma correção não precise ser
refeita à mão a cada versão.

```bash
cd documentacao/fontes
npm install docx        # única dependência
node montar.js          # gera DocumentacaoSmartCondo.docx nesta pasta
```

Depois é só mover o arquivo gerado para `documentacao/`.

### Quando o banco mudar

O diagrama entidade-relacionamento e o dicionário de dados são lidos do
banco em funcionamento. Depois de uma migração nova, com o PostgreSQL
no ar e as migrações aplicadas, refaça os dois antes do `node montar.js`:

```bash
cd documentacao/fontes/diagramas
pip install matplotlib             # só para os desenhos
python3 dicionario.py              # atualiza ../banco_gerado.js
python3 der.py                     # redesenha der_*.png
python3 casos_de_uso.py            # só se a lista de casos de uso mudar
```

O `dicionario.py` **para com erro** se encontrar uma coluna ou chave
estrangeira sem descrição em português. É proposital: escreva a
descrição no próprio script e rode de novo.

| Arquivo em `fontes/` | O que tem |
|---|---|
| `montar.js` | Monta o documento: formatação ABNT, sumário, tabelas, figuras e a ordem das 26 seções |
| `conteudo.js` | Capa, histórico de revisões, seções 1 a 8 e os casos de uso (seção 12) |
| `requisitos.js` | Requisitos funcionais (seção 9) e não funcionais (seção 10) |
| `conteudo2.js` | Ferramentas (seção 19) e as descrições das telas (seção 13) |
| `banco.js` | Textos do modelo entidade-relacionamento, dos relacionamentos e das implementações no banco (seções 14, 16 e 18) |
| `banco_gerado.js` | Dicionário de dados e relacionamentos — **gerado** por `diagramas/dicionario.py`, não edite à mão |
| `conteudo3.js` | Acessibilidade, arquitetura, API, testes, conclusão, cronograma e referências |
| `diagramas/` | Os scripts e as figuras do diagrama de casos de uso e do diagrama entidade-relacionamento |
| `telas/` | As 25 figuras das telas, capturadas do sistema em funcionamento |
| `previa.py` | Gera um HTML paginado a partir do `.docx`, para conferir o resultado sem abrir o Word |

```bash
python previa.py ../DocumentacaoSmartCondo.docx /tmp/previa.html
```
