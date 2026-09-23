# Contas de demonstração e como subir o sistema

Este arquivo existe para você abrir o SmartCondo, entrar com cada perfil e
acompanhar o que já está pronto em cada área.

> **Não está conseguindo entrar?** Abra a página
> **`frontend/diagnostico.html`** pelo mesmo servidor que você usa para
> abrir o sistema (Live Server ou `python -m http.server`). Ela testa
> cada peça sozinha e diz exatamente o que está faltando, com o comando
> para resolver.

---

## As contas

Todas usam a **mesma senha: `smartcondo123`**

| Perfil | E-mail | O que dá para acompanhar por ele |
|---|---|---|
| **Administrador** | `admin@smartcondo.com` | Cadastro de condomínios, código de acesso de cada um, criação da conta do síndico e a lista geral de usuários da plataforma |
| **Síndico** | `sindico@smartcondo.com` | Painel do condomínio, aprovação de moradores e de reservas, financeiro e inadimplência, comunicados, ordens de manutenção e resposta às ocorrências |
| **Porteiro** | `porteiro@smartcondo.com` | Entrada e saída de visitantes, encomendas, veículos e registro de ocorrências do turno |
| **Morador** | `morador@smartcondo.com` | Reservar áreas comuns, ver boletos, comunicados, documentos e abrir ocorrências |

### Contas extras, para ver o sistema com movimento

| E-mail | Perfil | Para que serve |
|---|---|---|
| `renata@smartcondo.com` | Porteiro | Está **sem** permissão de veículos e ocorrências — mostra o controle de permissões que o síndico configura |
| `ana@smartcondo.com` | Morador (Apto 301) | Outro morador, para ver reservas e cobranças de mais de uma unidade |
| `bruno@smartcondo.com` | Morador (Apto 102) | Idem |
| `marina@smartcondo.com` | Morador (Apto 410) | Idem |
| `pedro@smartcondo.com` | Morador (Apto 502) | Está **aguardando aprovação** — entre como síndico para aprovar ou recusar o cadastro dele |

### Código de acesso do condomínio

```
PALM-2025
```

É o que o morador informa ao se cadastrar sozinho, em *Criar conta →
Morador*. Quem se cadastra assim fica pendente até o síndico aprovar.

> Essas contas vêm do `backend/app/seed.py`. Se quiser zerar tudo e
> recriar, rode `python -m app.seed --limpar`.

---

## Subindo o sistema

São três coisas no ar ao mesmo tempo: o **banco**, a **API** e o
**front-end**.

### No Windows, em um comando só

O [`configurar.ps1`](configurar.ps1) faz todos os passos abaixo sozinho:
instala as dependências, cria o `.env`, cria o usuário e o banco no
PostgreSQL, cria as tabelas, carrega as contas de demonstração e sobe a
API. Rodar duas vezes não faz mal — ele pula o que já está pronto.

```powershell
powershell -ExecutionPolicy Bypass -File .\configurar.ps1
```

Ou dê dois cliques no `configurar.bat`, que chama o mesmo script.

Ele vai pedir a senha do usuário `postgres` (a que você escolheu ao
instalar o PostgreSQL) na primeira vez, e só nela. Se alguma peça estiver
faltando, ele diz qual é e o que fazer, em vez de estourar um erro
técnico.

O resto desta seção é o mesmo caminho na mão, para Linux, macOS ou para
quem quiser entender cada etapa.

### 1. Banco de dados (PostgreSQL)

Instale o PostgreSQL 16 e crie o banco e o usuário:

```sql
CREATE USER smartcondo WITH PASSWORD 'smartcondo';
CREATE DATABASE smartcondo OWNER smartcondo;
```

No Windows dá para fazer isso pelo pgAdmin, que vem junto com o instalador.

> **Atalho pelo pgAdmin, sem Python.** Os scripts de
> [`banco/`](banco/README.md) criam as tabelas e carregam as mesmas
> contas de demonstração: rode `01_criar_tabelas.sql` e depois
> `02_carga_dados.sql` no Query Tool. Quem faz por aí pode pular o
> `alembic upgrade head` e o `python -m app.seed` do passo 2.

### 2. API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env

alembic upgrade head             # cria as tabelas
python -m app.seed --limpar      # cria as contas acima

uvicorn app.main:app --reload
```

A API sobe em <http://localhost:8000> e a documentação interativa fica em
<http://localhost:8000/docs>. **Deixe este terminal aberto.**

### 3. Front-end

Em **outro terminal**, na pasta `frontend/`:

```bash
cd frontend
python -m http.server 8080
```

Abra <http://localhost:8080> e faça o login.

No VS Code, a extensão *Live Server* também serve — qualquer porta local
funciona.

---

## Quando o login falha

| O que aparece | O que é | Como resolver |
|---|---|---|
| "Não foi possível falar com o servidor. Verifique se a API está no ar." | O `uvicorn` não está rodando, ou caiu | Volte ao terminal da API e veja o erro. Confirme abrindo <http://localhost:8000/docs> |
| "E-mail ou senha incorretos" | A senha está certa mas o banco está vazio | Rode `python -m app.seed --limpar` |
| A tela carrega vazia, sem erro | O banco subiu sem os dados de demonstração | Idem: `python -m app.seed --limpar` |
| Erro de CORS no console do navegador | Front-end numa origem que a API não libera | Qualquer `localhost`/`127.0.0.1` já é liberado. Para abrir o `index.html` direto do disco (`file://`), deixe `DEBUG=true` no `.env` |
| `connection refused` no terminal da API | O PostgreSQL não está no ar | Inicie o serviço do PostgreSQL e confira a `DATABASE_URL` do `.env` |
| O código de confirmação não chega no e-mail | Falta configurar o SMTP | Com `DEBUG=true` o código aparece no terminal da API e volta na resposta. Para enviar de verdade, preencha `SMTP_HOST` no `.env` |

> Depois de rodar os testes (`pytest`), o banco fica vazio: os testes
> derrubam as tabelas no fim. Rode `alembic upgrade head` e
> `python -m app.seed --limpar` de novo antes de usar o sistema.
