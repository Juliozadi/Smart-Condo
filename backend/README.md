# SmartCondo — API

Back-end do SmartCondo, o Sistema de Gerenciamento de Condomínios
(Projeto Integrador I).

Conforme a documentação do projeto, o servidor é em **Python** (seção 10.4)
e o banco é **PostgreSQL** (seção 10.5).

| Camada | Escolha |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migrações | Alembic |
| Banco | PostgreSQL 16 |
| Autenticação | JWT (HS256) |
| Senha | bcrypt |
| Testes | pytest, contra um PostgreSQL de verdade |

---

## Como rodar

### 1. Banco

```bash
createdb smartcondo
createdb smartcondo_test        # usado pelos testes
```

### 2. Dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuração

```bash
cp .env.example .env
# gere uma SECRET_KEY própria:
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4. Migrações

```bash
alembic upgrade head
```

### 5. Dados de demonstração (opcional)

```bash
python -m app.seed             # cria um condomínio completo
python -m app.seed --limpar    # apaga tudo antes de criar
```

Cria síndico, dois porteiros com permissões diferentes, quatro moradores,
oito espaços, reservas, três competências de cobrança, comunicados e
movimento de portaria. Todas as contas saem com a senha `smartcondo123`, e
um cadastro fica aguardando aprovação para a tela do síndico ter o que
mostrar. Sem os `--limpar`, o comando se recusa a rodar num banco que já
tem dados.

### 6. Subir a API

```bash
uvicorn app.main:app --reload
```

- Documentação interativa: <http://localhost:8000/docs>
- Alternativa (ReDoc): <http://localhost:8000/redoc>

### 7. Testes

```bash
pytest
```

---

## Organização

```
backend/
├── alembic/                 # migrações
├── app/
│   ├── core/
│   │   ├── config.py        # configuração lida do ambiente
│   │   ├── database.py      # engine e sessão
│   │   └── security.py      # bcrypt, JWT e códigos de verificação
│   ├── models/              # tabelas (SQLAlchemy)
│   ├── schemas/             # entrada e saída (Pydantic)
│   ├── services/            # regras de negócio
│   ├── api/
│   │   ├── deps.py          # autenticação, papéis e permissões
│   │   └── routers/         # endpoints
│   └── main.py
└── tests/
```

---

## Endpoints por área

| Área | Prefixo | O que cobre na documentação |
|---|---|---|
| Autenticação | `/api/v1/auth` | Seção 9: Cadastro, Login, Esqueci minha senha |
| Condomínio | `/api/v1/condominios` | Seção 9: Cadastro do condomínio |
| Usuários | `/api/v1/usuarios` | Seções 8, 9 e 11.2: cadastro do porteiro, permissões e aprovação |
| Espaços e reservas | `/api/v1/espacos` | Seções 6 e 11.5.3: reservas sigilosas, ocupação e aprovação |
| Portaria | `/api/v1/portaria` | Seção 6: vídeo porteiro, encomendas e ocorrências |
| Financeiro | `/api/v1/financeiro` | Seção 6: cobrança na data escolhida e formas de pagamento |
| Comunicados | `/api/v1/comunicados` | Seções 11.5.4 e 11.6.4 |
| Veículos | `/api/v1/veiculos` | Seção 8: o porteiro controla entradas e saídas |
| Manutenção | `/api/v1/manutencao` | Ordens de serviço abertas pelo síndico |
| Documentos | `/api/v1/documentos` | Seção 11.6: atas, convenção e regimento |

---

## Regras que vêm da documentação

**Sigilo da reserva** — Seção 6: *"eu gostaria que não mostrasse quem
alugou, para evitar conflitos"*. `GET /espacos/agenda` devolve o espaço, a
data e o horário ocupados, sem nenhum campo de autoria. Nem a mensagem de
conflito de horário cita o outro morador. Quem enxerga o autor da reserva é
apenas o síndico, que é quem aprova (seção 13.5.3).

**Ocupação em tempo real** — Seção 6: *"Piscina: 23 pessoas no momento"*.
`GET /espacos/ocupacao` devolve a contagem mais recente de cada área de uso
livre, com capacidade e percentual.

**Vídeo porteiro** — Seção 6: o registro de visitante guarda a foto e nasce
como `aguardando_confirmacao`; só o morador da unidade visitada confirma ou
recusa a entrada.

**Permissão do Porteiro** — Seção 9: o síndico consulta as ações
disponíveis e escolhe quais libera. A API aplica isso em cada rota da
portaria; o acesso ao financeiro não vem ligado por padrão.

**Cobrança na data escolhida** — Seção 6: o morador define o dia do
vencimento e a forma de pagamento preferida, e a geração da cobrança usa
esse dia. Ao receber um pagamento, o síndico é notificado com o meio, quem
pagou e a data.

---

## Decisões de segurança

- Senha em **bcrypt**; o código de verificação também é guardado só em hash.
- O login responde a **mesma mensagem** para e-mail inexistente e senha
  errada, e o reenvio de código e a recuperação de senha não revelam quem
  está cadastrado.
- O destino do código volta **mascarado** (`ro*****@exemplo.com`).
- O código de verificação **expira** e tem limite de tentativas; emitir um
  novo invalida o anterior.
- **CPF e CNPJ** são validados pelos dígitos verificadores.
- A senha é limitada a 72 bytes no schema, que é o teto do bcrypt.
- Cada consulta é restrita ao condomínio do usuário; o morador só alcança a
  própria unidade.
- Usuários são **inativados**, nunca apagados, para o histórico de portaria,
  reservas e financeiro continuar íntegro.

> `DEBUG=true` faz o código de confirmação voltar na resposta do cadastro,
> para testar sem provedor de e-mail/SMS. **Nunca ligue isso em produção.**

---

## O que ainda falta

- Envio real de e-mail e SMS (hoje `app/services/notificacao.py` registra
  no log; a interface já é a definitiva).
- Upload das fotos do vídeo porteiro: a API guarda a URL, falta o
  armazenamento dos arquivos.
- Chat e chamada de voz com o porteiro (seção 13.5.2), que a documentação
  coloca em Node.js por serem em tempo real.
- Geração automática das cobranças mensais (tarefa agendada).
