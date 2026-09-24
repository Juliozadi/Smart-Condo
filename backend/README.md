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
python -m app.seed --limpar    # apaga tudo (inclusive os arquivos enviados) antes de criar
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
| Documentos | `/api/v1/documentos` | Seção 11.6: atas, convenção e regimento, com o arquivo protegido |
| Mensagens | `/api/v1/mensagens` | Seção 13.5.2: chat entre síndico, portaria e moradores |
| Arquivos | `/api/v1/arquivos` | Fotos de perfil (as da portaria e os documentos saem pelas próprias áreas) |

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

**Vídeo porteiro** — Seção 6: o registro de visitante nasce como
`aguardando_confirmacao`; só o morador da unidade visitada confirma ou
recusa a entrada. A foto vai logo depois, em
`PUT /portaria/visitantes/{id}/foto` (e `/encomendas/{id}/foto` para o
volume).

**Fotos da portaria e documentos do cadastro** — são dados pessoais de
terceiros, então não têm endereço público como a foto de perfil. Ficam em
`uploads/portaria` e `uploads/documentos` e só saem por rotas que conferem
o token: a foto do visitante vai para o morador da unidade, o síndico e o
porteiro com permissão de registrar visitantes; os documentos, só para o
síndico do condomínio. Respostas com `Cache-Control: private, no-store`.
As fotos passam de `FOTO_PORTARIA_DIAS` (90) e são apagadas; os documentos
saem quando o cadastro é recusado ou o usuário é inativado.

**Documentos do condomínio** — o síndico envia o arquivo (PDF ou imagem,
até `DOCUMENTO_MAX_KB`) em `POST /documentos`, como formulário com arquivo.
Fica em `uploads/condominio` e sai por `GET /documentos/{id}/arquivo`: o
documento de todos, para quem é do condomínio; o de uma unidade, só para
quem mora nela (e para o síndico).

**Foto da ocorrência** — `PUT /portaria/ocorrencias/{id}/foto`, só por quem
abriu e só até o síndico responder. Vê quem pode ver a ocorrência: quem
abriu, o síndico e o porteiro com a permissão de ocorrências.

**Limite de códigos** — no máximo um código por minuto
(`CODIGO_INTERVALO_S`) e cinco por hora (`CODIGO_MAX_POR_HORA`) por
pessoa e finalidade. Quando o limite barra o pedido, a resposta é a mesma
de sempre, para não revelar quem está cadastrado.

**Datas** — a API recusa reserva em horário de hoje que já passou ou com
mais de `RESERVA_ANTECEDENCIA_MAX_DIAS` (180) dias de antecedência,
cobrança com competência de mais de 5 anos atrás (prazo de prescrição) ou
mais de 12 meses à frente, vencimento antes da competência e data de
nascimento no futuro. "Hoje" e "agora" são os do relógio do servidor:
ao publicar, configure o fuso do servidor para o do condomínio
(por exemplo `TZ=America/Campo_Grande`).

**Envio dos documentos no cadastro** — quem acabou de se cadastrar ainda
não pode entrar, então `POST /auth/cadastro/morador` devolve um
`token_documentos`. Ele vale `TOKEN_DOCUMENTOS_MIN` (60) minutos, só serve
para `PUT /auth/cadastro/documentos/{tipo}` e `PUT /auth/cadastro/foto`,
deixa de valer quando o síndico decide e nunca abre sessão — nem depois da
aprovação.

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
- **Trocar ou redefinir a senha encerra as outras sessões**: o token leva a
  `versao_sessao` do usuário, que a troca aumenta. A troca pelo perfil
  devolve um token novo, e quem trocou segue conectado.
- Tentativas de login, palpites do código, pedidos de código, reservas e
  pagamentos travam a linha no banco (`SELECT ... FOR UPDATE`): requisições
  simultâneas entram uma por vez e não escapam dos limites.
- Valor que o banco recusa (id acima do limite, caractere nulo) responde
  **422**, e registro duplicado barrado por ele responde **409** — nunca 500.

> `DEBUG=true` faz o código de confirmação voltar na resposta do cadastro,
> para testar sem provedor de e-mail/SMS. **Nunca ligue isso em produção.**

---

## O que ainda falta

- Dados complementares do cadastro do morador (número do RG, contato de
  emergência, veículos, animais): o formulário pede, mas a API ainda não
  tem onde guardá-los.
- Chamada de voz dentro do navegador; hoje "Ligar" disca o telefone
  cadastrado.
- Geração automática das cobranças mensais (tarefa agendada).
