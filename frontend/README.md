# Front-end — SmartCondo

HTML, CSS e JavaScript puros: sem framework, sem build, sem dependência
externa. Basta servir esta pasta.

```bash
python servidor.py 8080         # a partir de frontend/
```

Abra <http://localhost:8080>. A API precisa estar no ar em
<http://localhost:8000> — veja [`../ACESSOS.md`](../ACESSOS.md).

## Organização

| Pasta | O que tem |
|---|---|
| `index.html` | Tela de login, a porta de entrada |
| `assets/css/` | `style.css` (global e login) e `dashboard.css` (telas internas) |
| `assets/js/` | Os seis módulos descritos abaixo |
| `assets/img/` | Logo e os 47 ícones SVG |
| `pages/cadastro/` | Cadastro do morador e confirmação por código |
| `pages/login/` | Recuperação de senha |
| `pages/morador/` | Telas do morador |
| `pages/porteiro/` | Telas do porteiro |
| `pages/sindico/` | Telas do síndico |
| `pages/admin/` | Telas do administrador |

## Os módulos JavaScript

| Arquivo | Responsabilidade |
|---|---|
| `api.js` | Única camada que fala com o back-end: URL base, token, envio e tratamento de erro |
| `sessao.js` | Guarda de rota e preenchimento do cabeçalho com o usuário logado |
| `admin-ui.js` | Modal, tabelas, filtros e formatação de datas e valores |
| `validation.js` | Validações e máscaras de CPF, telefone, CEP, CNPJ e placa |
| `foto.js` | Captura de foto pela câmera (vídeo porteiro) |
| `acessibilidade.js` | Tema claro/escuro, tamanho de fonte, alto contraste e VLibras |

Nenhuma tela chama `fetch()` direto: tudo passa por `api.js`, para que
token e erro tenham um tratamento só.

## Onde fica a URL da API

`api.js` monta a URL a partir do host da página, na porta 8000. Para
apontar para outro servidor, defina a variável antes de carregar o
script:

```html
<script>window.SMARTCONDO_API = 'https://api.exemplo.com/api/v1';</script>
<script src="assets/js/api.js"></script>
```

## Cores e contraste

As cores vivem em variáveis CSS, definidas em `:root` (tema claro) e
redefinidas em `body.tema-escuro` e `body.alto-contraste`. **Nunca
escreva um valor de cor direto numa regra** — se escrever, a cor não
acompanha a troca de tema, e foi exatamente isso que deixou os títulos
do login ilegíveis no modo escuro.

Para texto, use os tokens semânticos:

| Token | Para que serve |
|---|---|
| `--text`, `--text-2`, `--muted` | Texto comum, secundário e de apoio |
| `--placeholder` | Texto de dica dentro de campos |
| `--sucesso`, `--aviso`, `--erro`, `--info` | Estados |
| `--primary-texto` | O teal da marca **como texto** |
| `--primary-botao` + `--sobre-primary` | Fundo teal com texto por cima |

O `--primary` puro (`#079e92`) tem só 3,33:1 sobre o branco: serve de
cor de marca em fundo, borda e ícone, não de cor de texto.

Cada valor foi escolhido por busca, até passar os 4,5:1 do WCAG AA em
todos os fundos onde a cor de fato aparece — as superfícies do tema, as
tintas translúcidas dos badges e as pílulas. No modo alto contraste os
mesmos tokens valem 7:1 (AAA).

### Conferindo

`ferramentas/contraste.js` percorre as 38 páginas nos dois temas, mede o
contraste de cada texto visível e lista o que não alcança o mínimo.
Rode sempre que mexer em cor:

```bash
# com a API (8000) e o front-end (8080) no ar
npm install playwright
node ferramentas/contraste.js
```

Sai com código 1 se achar alguma falha, agrupada por causa — a mesma
cor sobre o mesmo fundo aparece uma vez, não uma por ocorrência.
Fundos em gradiente são pulados: com a cor variando ao longo do
elemento, não dá para apurar a razão com honestidade.

## Testes de interface

`testes/` abre as telas num navegador de verdade e confere o que já
quebrou uma vez: erro de JavaScript, imagem quebrada, rolagem lateral no
celular, barra superior fora do topo, ícones faltando, fundo claro no
tema escuro e o medidor de senha do cadastro. Rodam a cada envio ao
GitHub; para rodar na sua máquina, com a API e o site no ar:

```bash
pip install -r testes/requirements.txt
python -m playwright install chromium
python -m pytest testes
```
