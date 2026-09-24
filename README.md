<div align="center">
  <img src="frontend/assets/img/logo.png" alt="SmartCondo Logo" width="80">
  <h1 align="center">SmartCondo</h1>
  <p align="center"><strong>Sistema de Gestão de Condomínios</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/status-em%20desenvolvimento-yellow" alt="Status: Em desenvolvimento">
    <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=fff" alt="HTML5">
    <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=fff" alt="CSS3">
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=000" alt="JavaScript">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff" alt="FastAPI">
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=fff" alt="PostgreSQL">
    <img src="https://github.com/Juliozadi/Smart-Condo/actions/workflows/testes.yml/badge.svg" alt="Testes">
    <img src="https://img.shields.io/badge/licença-MIT-blue" alt="Licença MIT">
  </p>
</div>

---

## 📋 Sobre o Projeto

O **SmartCondo** é um sistema de gestão condominial desenvolvido como projeto integrador da faculdade. A plataforma centraliza em um único lugar todas as atividades relacionadas à administração de um condomínio, oferecendo quatro perfis de acesso com funcionalidades específicas para cada tipo de usuário.

O projeto tem duas partes. O **front-end** é construído com tecnologias web puras — sem frameworks nem bibliotecas externas — e o **back-end** é uma API REST em Python com PostgreSQL, como define a documentação do projeto (seções 19.4 e 19.5).

---

## 🎯 Funcionalidades por Perfil

### 🏠 Morador
- **Dashboard** — Visão geral com reservas, financeiro e comunicados
- **Reservas** — Agendamento de áreas comuns (salão, churrasqueira, piscina, academia, playground)
- **Financeiro** — Visualização de boletos, saldo devedor e histórico de pagamentos
- **Comunicados** — Acompanhamento de avisos do condomínio com filtros por categoria
- **Documentos** — Acesso a atas, convenção e regimento interno
- **Ocorrências** — Abertura e acompanhamento de solicitações
- **Perfil** — Edição de dados pessoais e alteração de senha

### 🚪 Porteiro
- **Dashboard** — Visão geral de visitantes, encomendas e comunicados
- **Visitantes** — Controle de entrada e saída de visitantes
- **Encomendas** — Registro e controle de retirada de encomendas
- **Veículos** — Controle de entrada e saída de veículos
- **Ocorrências** — Registro de ocorrências durante o turno
- **Perfil** — Edição de dados pessoais

### 📊 Síndico
- **Dashboard** — Painel administrativo com indicadores do condomínio
- **Financeiro** — Gestão financeira completa, geração de boletos e inadimplência
- **Moradores** — Cadastro e aprovação de novos moradores
- **Porteiros** — Gestão da equipe de portaria
- **Reservas** — Aprovação ou recusa de reservas
- **Comunicados** — Criação e envio de comunicados
- **Manutenção** — Abertura e acompanhamento de ordens de serviço
- **Ocorrências** — Resposta aos chamados de moradores e porteiros
- **Perfil** — Edição de dados pessoais e troca de senha

### ⭐ Administrador
- **Dashboard** — Indicadores da plataforma inteira
- **Condomínios** — Cadastro dos condomínios e do código de acesso de cada um
- **Usuários** — Criação da conta do síndico e apoio na gestão de porteiros e moradores

> A hierarquia de cadastro: o **administrador** cria o síndico junto com o
> condomínio, o **síndico** cadastra porteiros e moradores, e o **morador**
> também pode se cadastrar sozinho com o código do condomínio, ficando
> pendente de aprovação do síndico.

---

## 📄 Documentação

A documentação do Projeto Integrador I está em
[`documentacao/`](documentacao/), em formato Word e seguindo a ABNT. O
arquivo [`ALTERACOES.md`](documentacao/ALTERACOES.md) registra o que mudou
em relação à versão anterior.

Ao abrir no Word, atualize o sumário (botão direito sobre ele → *Atualizar
campo* → *Atualizar o índice inteiro*) para que os números de página sejam
calculados.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
|---|---|
| **HTML5** | Estrutura semântica e multi-step forms com `:target` |
| **CSS3** | Design system com variáveis, glassmorphism, animações e responsividade |
| **JavaScript** | Validação de formulários, máscaras de input, acessibilidade e interatividade |
| **LocalStorage** | Persistência de preferências de acessibilidade e nome do perfil |
| **VLibras** | Tradução do conteúdo para Libras (documentação, seção 12.2) |
| **Python / FastAPI** | API REST do back-end (documentação, seção 10.4) |
| **PostgreSQL** | Banco de dados (documentação, seção 10.5) |
| **SQLAlchemy / Alembic** | ORM e migrações |
| **Google Fonts** | Plus Jakarta Sans (única fonte do projeto) |
| **SVG** | 47 ícones customizados |

O **front-end** não usa frameworks, build tools nem dependências externas: apenas HTML, CSS e JavaScript puros. O **back-end** fica em `backend/` e tem README próprio.

---

## 🎨 Destaques do Projeto

- **Design system completo** — Variáveis CSS para cores, sombras, bordas e espaçamentos
- **Detecção de perfil em tempo real** — Ao digitar a senha, o sistema identifica automaticamente o perfil
- **Multi-step forms** — Navegação entre etapas de cadastro usando CSS `:target`
- **Acessibilidade** — VLibras, modo claro/escuro seguindo o sistema operacional, aumento de fonte, alto contraste e modo leitura
- **Glassmorphism** — Barra superior com efeito de vidro (`backdrop-filter: blur`)
- **Layout responsivo** — Duas variações: `layout-mobile` (bottom tab bar) e `layout-desktop`
- **Micro-interações** — Hover lifts, shimmer, pulse em badges e animações suaves
- **Três temas de cor** — Verde (morador), azul (porteiro) e roxo (síndico)
- **Máscaras de input** — CPF, telefone, CEP, CNPJ e placa de veículo

---

## 📁 Estrutura do Projeto

```
SmartCondo/
├── frontend/                          # Interface (HTML, CSS e JS puros)
├── backend/                           # API REST em FastAPI
├── banco/                             # Scripts SQL para o pgAdmin
├── documentacao/                      # Documento ABNT do Projeto Integrador
├── ACESSOS.md                         # Contas de demonstração e como subir
└── README.md
```

Cada pasta tem o seu próprio README com as instruções específicas.

### `frontend/`

```
frontend/
├── index.html                         # Página de login
├── 404.html                           # Endereço inexistente
├── diagnostico.html                   # Confere se a API responde
├── assets/
│   ├── css/
│   │   ├── style.css                  # Estilos globais e login
│   │   └── dashboard.css              # Estilos dos dashboards
│   ├── js/
│   │   ├── api.js                     # Cliente da API: token, erros e rotas
│   │   ├── sessao.js                  # Guarda de rota e dados do cabeçalho
│   │   ├── admin-ui.js                # Modal, tabelas e formatações
│   │   ├── validation.js              # Validações e máscaras de input
│   │   ├── foto.js                    # Captura de foto (vídeo porteiro)
│   │   ├── foto-perfil.js             # Envio e troca da foto de perfil
│   │   ├── chat.js                    # Mensagens entre os perfis
│   │   ├── permissoes.js              # O que o porteiro pode registrar
│   │   └── acessibilidade.js          # Acessibilidade, VLibras e tema
│   └── img/
│       ├── logo.png
│       ├── acessibilidade.png
│       └── icons/                     # 43 ícones SVG
└── pages/
    ├── legal/                         # Termos de uso e privacidade
    ├── cadastro/                      # Cadastro de usuários (3 páginas)
    ├── login/                         # Recuperação de senha (3 páginas)
    ├── morador/                       # Módulo do morador (8 páginas)
    ├── porteiro/                      # Módulo do porteiro (7 páginas)
    ├── sindico/                       # Módulo do síndico (14 páginas)
    └── admin/                         # Módulo do administrador (3 páginas)
```

### `backend/`

```
backend/
├── alembic/                           # Migrações do banco
├── app/
│   ├── core/                          # Configuração, banco e segurança
│   ├── models/                        # 21 tabelas
│   ├── schemas/                       # Entrada e saída da API
│   ├── services/                      # Regras de negócio
│   ├── api/routers/                   # Endpoints
│   ├── seed.py                        # Dados de demonstração
│   └── main.py
└── tests/                             # 354 casos de teste
```

**Total:** 43 páginas HTML, 2 arquivos CSS, 9 arquivos JS, 43 ícones SVG e
uma API com 99 endpoints.

---

## 🗄️ Back-end

A API fica em [`backend/`](backend/), com instruções completas no
[README do back-end](backend/README.md).

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ajuste a SECRET_KEY e a DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

Documentação interativa da API em <http://localhost:8000/docs>.

**99 endpoints**, cobrindo os casos de uso e as histórias de usuário da
documentação — cadastro com código de confirmação, login, recuperação de
senha, cadastro do condomínio, permissões do porteiro, reservas sigilosas,
ocupação das áreas em tempo real, vídeo porteiro, encomendas, financeiro e
comunicados, documentos e chat. **354 casos de teste** rodando contra PostgreSQL, a cada push, pelo GitHub Actions.

---

## 🚀 Como Executar

O sistema tem três partes no ar ao mesmo tempo: o **banco**, a **API** e o
**front-end**. O passo a passo completo, com as contas de demonstração,
está em **[`ACESSOS.md`](ACESSOS.md)**.

Em resumo:

```bash
git clone https://github.com/Juliozadi/Smart-Condo.git
cd Smart-Condo

# 1. API (precisa do PostgreSQL rodando)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed --limpar
uvicorn app.main:app --reload

# 2. Front-end, em outro terminal, na pasta frontend/
cd frontend
python servidor.py 8080
```

Abra <http://localhost:8080> e entre com uma das contas de demonstração —
todas com a senha `smartcondo123`:

| Perfil | E-mail |
|---|---|
| Administrador | `admin@smartcondo.com` |
| Síndico | `sindico@smartcondo.com` |
| Porteiro | `porteiro@smartcondo.com` |
| Morador | `morador@smartcondo.com` |

> As telas leem e gravam pela API — **sem a API no ar o login não
> funciona**. Se aparecer *"Não foi possível falar com o servidor"*, é
> isso. Veja [`ACESSOS.md`](ACESSOS.md).

---

## 📌 Funcionalidades Futuras

- [x] Implementação de backend com API REST
- [x] Autenticação com JWT
- [x] Banco de dados real (PostgreSQL)
- [x] Envio real de e-mail (SMTP)
- [x] Envio de SMS (Twilio, opcional, configurado no `.env`)
- [x] Foto de perfil
- [x] Fotos do visitante e da encomenda, vistas só pela portaria, pelo síndico e pelo morador da unidade, e apagadas depois de 90 dias
- [x] Documentos do cadastro do morador (RG, comprovante, escritura), conferidos pelo síndico antes de aprovar
- [ ] Dados complementares do cadastro do morador (número do RG, contato de emergência, veículos, animais): o formulário pede, mas a API ainda não os guarda
- [x] Integrar as telas do front-end à API
- [x] Chat entre síndico, porteiros e moradores, e ligação pelo telefone cadastrado
- [ ] Chamada de voz dentro do navegador (exige servidor de mídia)
- [ ] Notificações push
- [ ] Painel de gráficos com dados dinâmicos
- [ ] Aplicativo mobile (React Native)
- [ ] Integração com sistemas de portaria física

---

## 👥 Autores

Projeto Integrador I, desenvolvido por:

- Júlio César Zadi de Assis dos Santos
- Joao Victor Muller Miranda
- Luan Flores Martins
- Lenini Bellodi Júnior
- Juliano dos Santos Apolinario Araujo

---

## 📜 Licença

Distribuído sob a [licença MIT](LICENSE) — o código pode ser usado,
copiado e modificado, inclusive comercialmente, desde que o aviso de
autoria seja mantido.

---

<div align="center">
  <p>Projeto Integrador — Faculdade</p>
</div>
