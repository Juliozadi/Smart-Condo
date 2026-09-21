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

| Arquivo em `fontes/` | O que tem |
|---|---|
| `montar.js` | Monta o documento: formatação ABNT, sumário, tabelas e figuras |
| `conteudo.js` | Capa, seções 1 a 10 e os casos de uso |
| `conteudo2.js` | Ferramentas e as descrições das telas (seção 11) |
| `conteudo3.js` | Acessibilidade, arquitetura, API, testes, conclusão, cronograma e referências |
| `telas/` | As 25 figuras, capturadas do sistema em funcionamento |
| `previa.py` | Gera um HTML paginado a partir do `.docx`, para conferir o resultado sem abrir o Word |

```bash
python previa.py ../DocumentacaoSmartCondo.docx /tmp/previa.html
```
