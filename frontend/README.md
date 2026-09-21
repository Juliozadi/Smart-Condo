# Front-end — SmartCondo

HTML, CSS e JavaScript puros: sem framework, sem build, sem dependência
externa. Basta servir esta pasta.

```bash
python -m http.server 8080      # a partir de frontend/
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
