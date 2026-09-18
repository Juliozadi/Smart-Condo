-- ═══════════════════════════════════════════════════════════════════
-- SmartCondo — Criação das tabelas
-- Sistema de Gerenciamento de Condomínios (Projeto Integrador I)
--
-- Banco: PostgreSQL 16
--
-- Como executar no pgAdmin:
--   1. Crie o banco:  botão direito em Databases > Create > Database
--                     com o nome  smartcondo
--   2. Selecione o banco smartcondo
--   3. Abra Tools > Query Tool
--   4. Abra este arquivo (ícone de pasta) e execute (F5)
--   5. Depois, execute o arquivo 02_carga_dados.sql
--
-- O script pode ser executado mais de uma vez: ele apaga o que existir
-- antes de recriar.
-- ═══════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────
-- 1. LIMPEZA
-- Remove as estruturas anteriores para o script poder ser reexecutado.
-- ───────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS
    ocorrencias,
    encomendas,
    visitantes,
    leituras_comunicado,
    comunicados,
    pagamentos,
    cobrancas,
    preferencias_cobranca,
    registros_ocupacao,
    reservas,
    espacos_comuns,
    codigos_verificacao,
    permissoes_porteiro,
    unidades,
    usuarios,
    condominios
CASCADE;

DROP TYPE IF EXISTS
    canal_verificacao,
    categoria_comunicado,
    finalidade_codigo,
    forma_pagamento,
    papel_usuario,
    status_cobranca,
    status_encomenda,
    status_ocorrencia,
    status_reserva,
    status_usuario,
    status_visitante,
    tipo_ocupacao
CASCADE;


-- ───────────────────────────────────────────────────────────────────
-- 2. TIPOS ENUMERADOS
-- Valores fixos usados nas colunas de papel, status e categoria.
-- ───────────────────────────────────────────────────────────────────

CREATE TYPE canal_verificacao AS ENUM (
    'EMAIL',
    'SMS'
);

CREATE TYPE categoria_comunicado AS ENUM (
    'GERAL',
    'MANUTENCAO',
    'FINANCEIRO',
    'SEGURANCA',
    'EVENTO',
    'URGENTE'
);

CREATE TYPE finalidade_codigo AS ENUM (
    'CONFIRMACAO_CADASTRO',
    'RECUPERACAO_SENHA'
);

CREATE TYPE forma_pagamento AS ENUM (
    'PIX',
    'BOLETO',
    'DEBITO_AUTOMATICO',
    'CARTAO'
);

CREATE TYPE papel_usuario AS ENUM (
    'SINDICO',
    'PORTEIRO',
    'MORADOR',
    'ADMIN'
);

CREATE TYPE status_cobranca AS ENUM (
    'ABERTA',
    'PAGA',
    'VENCIDA',
    'CANCELADA'
);

CREATE TYPE status_encomenda AS ENUM (
    'AGUARDANDO_RETIRADA',
    'RETIRADA',
    'RECUSADA'
);

CREATE TYPE status_ocorrencia AS ENUM (
    'ABERTA',
    'EM_ANALISE',
    'RESOLVIDA',
    'ARQUIVADA'
);

CREATE TYPE status_reserva AS ENUM (
    'PENDENTE',
    'APROVADA',
    'RECUSADA',
    'CANCELADA',
    'CONCLUIDA'
);

CREATE TYPE status_usuario AS ENUM (
    'AGUARDANDO_CODIGO',
    'AGUARDANDO_APROVACAO',
    'ATIVO',
    'RECUSADO',
    'INATIVO'
);

CREATE TYPE status_visitante AS ENUM (
    'AGUARDANDO_CONFIRMACAO',
    'CONFIRMADO',
    'RECUSADO',
    'DENTRO',
    'SAIU'
);

CREATE TYPE tipo_ocupacao AS ENUM (
    'PROPRIETARIO',
    'INQUILINO',
    'COABITANTE'
);


-- ───────────────────────────────────────────────────────────────────
-- 3. TABELAS
-- Cada tabela nasce com a chave primária, os campos obrigatórios e as
-- restrições de valor (CHECK). As chaves estrangeiras vêm na seção 4,
-- porque condominios e usuarios referenciam uma à outra.
-- ───────────────────────────────────────────────────────────────────


-- CONDOMINIOS — Condomínios cadastrados pelo administrador da plataforma.
CREATE TABLE condominios (
    id integer NOT NULL,
    nome character varying(160) NOT NULL,
    cnpj character varying(18) NOT NULL,
    cep character varying(9) NOT NULL,
    logradouro character varying(180) NOT NULL,
    numero character varying(20) NOT NULL,
    complemento character varying(80),
    bairro character varying(100) NOT NULL,
    cidade character varying(100) NOT NULL,
    uf character varying(2) NOT NULL,
    telefone character varying(20),
    sindico_id integer,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    codigo_acesso character varying(20) NOT NULL
);

CREATE SEQUENCE condominios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE condominios_id_seq OWNED BY condominios.id;
ALTER TABLE ONLY condominios ALTER COLUMN id SET DEFAULT nextval('condominios_id_seq'::regclass);

ALTER TABLE ONLY condominios
    ADD CONSTRAINT condominios_pkey PRIMARY KEY (id);


-- USUARIOS — Administradores, síndicos, porteiros e moradores.
CREATE TABLE usuarios (
    id integer NOT NULL,
    nome character varying(160) NOT NULL,
    email character varying(180) NOT NULL,
    cpf character varying(14) NOT NULL,
    telefone character varying(20) NOT NULL,
    data_nascimento date,
    senha_hash character varying(120) NOT NULL,
    papel papel_usuario NOT NULL,
    status status_usuario NOT NULL,
    condominio_id integer,
    unidade_id integer,
    tipo_ocupacao tipo_ocupacao,
    foto_url character varying(500),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE usuarios_id_seq OWNED BY usuarios.id;
ALTER TABLE ONLY usuarios ALTER COLUMN id SET DEFAULT nextval('usuarios_id_seq'::regclass);

ALTER TABLE ONLY usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


-- UNIDADES — Apartamentos ou casas de cada condomínio.
CREATE TABLE unidades (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    numero character varying(20) NOT NULL,
    bloco character varying(20) NOT NULL,
    andar integer,
    vagas_garagem integer NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE unidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE unidades_id_seq OWNED BY unidades.id;
ALTER TABLE ONLY unidades ALTER COLUMN id SET DEFAULT nextval('unidades_id_seq'::regclass);

ALTER TABLE ONLY unidades
    ADD CONSTRAINT unidades_pkey PRIMARY KEY (id);
ALTER TABLE ONLY unidades
    ADD CONSTRAINT uq_unidade_no_condominio UNIQUE (condominio_id, bloco, numero);


-- PERMISSOES_PORTEIRO — O que cada porteiro pode fazer, definido pelo síndico.
CREATE TABLE permissoes_porteiro (
    id integer NOT NULL,
    porteiro_id integer NOT NULL,
    registrar_visitantes boolean NOT NULL,
    registrar_encomendas boolean NOT NULL,
    registrar_veiculos boolean NOT NULL,
    registrar_ocorrencias boolean NOT NULL,
    acessar_financeiro boolean NOT NULL,
    definidas_por_id integer,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE permissoes_porteiro_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE permissoes_porteiro_id_seq OWNED BY permissoes_porteiro.id;
ALTER TABLE ONLY permissoes_porteiro ALTER COLUMN id SET DEFAULT nextval('permissoes_porteiro_id_seq'::regclass);

ALTER TABLE ONLY permissoes_porteiro
    ADD CONSTRAINT permissoes_porteiro_pkey PRIMARY KEY (id);


-- CODIGOS_VERIFICACAO — Códigos enviados por e-mail ou SMS (guardados em hash).
CREATE TABLE codigos_verificacao (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    codigo_hash character varying(64) NOT NULL,
    finalidade finalidade_codigo NOT NULL,
    canal canal_verificacao NOT NULL,
    expira_em timestamp with time zone NOT NULL,
    consumido_em timestamp with time zone,
    tentativas integer NOT NULL,
    destino text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE codigos_verificacao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE codigos_verificacao_id_seq OWNED BY codigos_verificacao.id;
ALTER TABLE ONLY codigos_verificacao ALTER COLUMN id SET DEFAULT nextval('codigos_verificacao_id_seq'::regclass);

ALTER TABLE ONLY codigos_verificacao
    ADD CONSTRAINT codigos_verificacao_pkey PRIMARY KEY (id);


-- ESPACOS_COMUNS — Salão, churrasqueira, piscina, academia e demais áreas.
CREATE TABLE espacos_comuns (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    nome character varying(120) NOT NULL,
    descricao text,
    capacidade integer NOT NULL,
    reservavel boolean NOT NULL,
    uso_livre boolean NOT NULL,
    em_manutencao boolean NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE espacos_comuns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE espacos_comuns_id_seq OWNED BY espacos_comuns.id;
ALTER TABLE ONLY espacos_comuns ALTER COLUMN id SET DEFAULT nextval('espacos_comuns_id_seq'::regclass);

ALTER TABLE ONLY espacos_comuns
    ADD CONSTRAINT espacos_comuns_pkey PRIMARY KEY (id);


-- RESERVAS — Pedidos de reserva dos espaços, aprovados ou recusados pelo síndico.
CREATE TABLE reservas (
    id integer NOT NULL,
    espaco_id integer NOT NULL,
    morador_id integer NOT NULL,
    data date NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fim time without time zone NOT NULL,
    pessoas_estimadas integer,
    observacoes text,
    status status_reserva NOT NULL,
    avaliada_por_id integer,
    avaliada_em timestamp with time zone,
    motivo_recusa text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_reserva_intervalo CHECK ((hora_fim > hora_inicio))
);

CREATE SEQUENCE reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE reservas_id_seq OWNED BY reservas.id;
ALTER TABLE ONLY reservas ALTER COLUMN id SET DEFAULT nextval('reservas_id_seq'::regclass);

ALTER TABLE ONLY reservas
    ADD CONSTRAINT reservas_pkey PRIMARY KEY (id);


-- REGISTROS_OCUPACAO — Contagem de pessoas nas áreas de uso livre, em tempo real.
CREATE TABLE registros_ocupacao (
    id integer NOT NULL,
    espaco_id integer NOT NULL,
    pessoas integer NOT NULL,
    registrado_em timestamp with time zone NOT NULL,
    registrado_por_id integer,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ocupacao_nao_negativa CHECK ((pessoas >= 0))
);

CREATE SEQUENCE registros_ocupacao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE registros_ocupacao_id_seq OWNED BY registros_ocupacao.id;
ALTER TABLE ONLY registros_ocupacao ALTER COLUMN id SET DEFAULT nextval('registros_ocupacao_id_seq'::regclass);

ALTER TABLE ONLY registros_ocupacao
    ADD CONSTRAINT registros_ocupacao_pkey PRIMARY KEY (id);


-- PREFERENCIAS_COBRANCA — Dia do vencimento e forma de pagamento escolhidos pelo morador.
CREATE TABLE preferencias_cobranca (
    id integer NOT NULL,
    morador_id integer NOT NULL,
    dia_vencimento integer NOT NULL,
    forma_preferida forma_pagamento NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_dia_vencimento CHECK (((dia_vencimento >= 1) AND (dia_vencimento <= 28)))
);

CREATE SEQUENCE preferencias_cobranca_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE preferencias_cobranca_id_seq OWNED BY preferencias_cobranca.id;
ALTER TABLE ONLY preferencias_cobranca ALTER COLUMN id SET DEFAULT nextval('preferencias_cobranca_id_seq'::regclass);

ALTER TABLE ONLY preferencias_cobranca
    ADD CONSTRAINT preferencias_cobranca_pkey PRIMARY KEY (id);


-- COBRANCAS — Taxa condominial por unidade e competência.
CREATE TABLE cobrancas (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    competencia date NOT NULL,
    descricao character varying(180) NOT NULL,
    valor numeric(10,2) NOT NULL,
    vencimento date NOT NULL,
    status status_cobranca NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_cobranca_valor_positivo CHECK ((valor > (0)::numeric))
);

CREATE SEQUENCE cobrancas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE cobrancas_id_seq OWNED BY cobrancas.id;
ALTER TABLE ONLY cobrancas ALTER COLUMN id SET DEFAULT nextval('cobrancas_id_seq'::regclass);

ALTER TABLE ONLY cobrancas
    ADD CONSTRAINT cobrancas_pkey PRIMARY KEY (id);
ALTER TABLE ONLY cobrancas
    ADD CONSTRAINT uq_cobranca_competencia UNIQUE (unidade_id, competencia);


-- PAGAMENTOS — Pagamentos recebidos, com meio, valor e data.
CREATE TABLE pagamentos (
    id integer NOT NULL,
    cobranca_id integer NOT NULL,
    pago_por_id integer,
    valor numeric(10,2) NOT NULL,
    forma forma_pagamento NOT NULL,
    pago_em timestamp with time zone NOT NULL,
    comprovante_url character varying(500),
    observacao text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_pagamento_valor_positivo CHECK ((valor > (0)::numeric))
);

CREATE SEQUENCE pagamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE pagamentos_id_seq OWNED BY pagamentos.id;
ALTER TABLE ONLY pagamentos ALTER COLUMN id SET DEFAULT nextval('pagamentos_id_seq'::regclass);

ALTER TABLE ONLY pagamentos
    ADD CONSTRAINT pagamentos_pkey PRIMARY KEY (id);


-- COMUNICADOS — Avisos publicados pelo síndico.
CREATE TABLE comunicados (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    autor_id integer NOT NULL,
    titulo character varying(180) NOT NULL,
    conteudo text NOT NULL,
    categoria categoria_comunicado NOT NULL,
    fixado boolean NOT NULL,
    publicado_em timestamp with time zone NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE comunicados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE comunicados_id_seq OWNED BY comunicados.id;
ALTER TABLE ONLY comunicados ALTER COLUMN id SET DEFAULT nextval('comunicados_id_seq'::regclass);

ALTER TABLE ONLY comunicados
    ADD CONSTRAINT comunicados_pkey PRIMARY KEY (id);


-- LEITURAS_COMUNICADO — Marca que um morador leu determinado comunicado.
CREATE TABLE leituras_comunicado (
    id integer NOT NULL,
    comunicado_id integer NOT NULL,
    usuario_id integer NOT NULL,
    lido_em timestamp with time zone NOT NULL
);

CREATE SEQUENCE leituras_comunicado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE leituras_comunicado_id_seq OWNED BY leituras_comunicado.id;
ALTER TABLE ONLY leituras_comunicado ALTER COLUMN id SET DEFAULT nextval('leituras_comunicado_id_seq'::regclass);

ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT leituras_comunicado_pkey PRIMARY KEY (id);
ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT uq_leitura_por_usuario UNIQUE (comunicado_id, usuario_id);


-- VISITANTES — Registro de visitantes, com a foto do vídeo porteiro.
CREATE TABLE visitantes (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    registrado_por_id integer,
    nome character varying(160) NOT NULL,
    documento character varying(20) NOT NULL,
    tipo_visita character varying(60) NOT NULL,
    placa_veiculo character varying(10),
    foto_url character varying(500),
    status status_visitante NOT NULL,
    entrada_em timestamp with time zone,
    saida_em timestamp with time zone,
    confirmado_por_id integer,
    confirmado_em timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE visitantes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE visitantes_id_seq OWNED BY visitantes.id;
ALTER TABLE ONLY visitantes ALTER COLUMN id SET DEFAULT nextval('visitantes_id_seq'::regclass);

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_pkey PRIMARY KEY (id);


-- ENCOMENDAS — Encomendas recebidas na portaria.
CREATE TABLE encomendas (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    registrada_por_id integer,
    remetente character varying(120) NOT NULL,
    tipo_volume character varying(60) NOT NULL,
    codigo_rastreio character varying(60),
    observacoes text,
    foto_url character varying(500),
    status status_encomenda NOT NULL,
    recebida_em timestamp with time zone NOT NULL,
    retirada_em timestamp with time zone,
    retirada_por_id integer,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE encomendas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE encomendas_id_seq OWNED BY encomendas.id;
ALTER TABLE ONLY encomendas ALTER COLUMN id SET DEFAULT nextval('encomendas_id_seq'::regclass);

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_pkey PRIMARY KEY (id);


-- OCORRENCIAS — Chamados abertos por moradores, porteiros ou síndico.
CREATE TABLE ocorrencias (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    aberta_por_id integer NOT NULL,
    unidade_id integer,
    titulo character varying(180) NOT NULL,
    descricao text NOT NULL,
    categoria character varying(60) NOT NULL,
    foto_url character varying(500),
    status status_ocorrencia NOT NULL,
    resposta text,
    respondida_por_id integer,
    respondida_em timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE ocorrencias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE ocorrencias_id_seq OWNED BY ocorrencias.id;
ALTER TABLE ONLY ocorrencias ALTER COLUMN id SET DEFAULT nextval('ocorrencias_id_seq'::regclass);

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_pkey PRIMARY KEY (id);


-- ───────────────────────────────────────────────────────────────────
-- 4. CHAVES ESTRANGEIRAS
-- Aplicadas depois de todas as tabelas existirem: condominios aponta
-- para o síndico em usuarios, e usuarios aponta para condominios.
-- ───────────────────────────────────────────────────────────────────

ALTER TABLE ONLY cobrancas
    ADD CONSTRAINT cobrancas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY codigos_verificacao
    ADD CONSTRAINT codigos_verificacao_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY comunicados
    ADD CONSTRAINT comunicados_autor_id_fkey FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY comunicados
    ADD CONSTRAINT comunicados_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY condominios
    ADD CONSTRAINT fk_condominios_sindico_id FOREIGN KEY (sindico_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_registrada_por_id_fkey FOREIGN KEY (registrada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_retirada_por_id_fkey FOREIGN KEY (retirada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY espacos_comuns
    ADD CONSTRAINT espacos_comuns_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT leituras_comunicado_comunicado_id_fkey FOREIGN KEY (comunicado_id) REFERENCES comunicados(id) ON DELETE CASCADE;

ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT leituras_comunicado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_aberta_por_id_fkey FOREIGN KEY (aberta_por_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_respondida_por_id_fkey FOREIGN KEY (respondida_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE SET NULL;

ALTER TABLE ONLY pagamentos
    ADD CONSTRAINT pagamentos_cobranca_id_fkey FOREIGN KEY (cobranca_id) REFERENCES cobrancas(id) ON DELETE CASCADE;

ALTER TABLE ONLY pagamentos
    ADD CONSTRAINT pagamentos_pago_por_id_fkey FOREIGN KEY (pago_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY permissoes_porteiro
    ADD CONSTRAINT permissoes_porteiro_definidas_por_id_fkey FOREIGN KEY (definidas_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY permissoes_porteiro
    ADD CONSTRAINT permissoes_porteiro_porteiro_id_fkey FOREIGN KEY (porteiro_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY preferencias_cobranca
    ADD CONSTRAINT preferencias_cobranca_morador_id_fkey FOREIGN KEY (morador_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY registros_ocupacao
    ADD CONSTRAINT registros_ocupacao_espaco_id_fkey FOREIGN KEY (espaco_id) REFERENCES espacos_comuns(id) ON DELETE CASCADE;

ALTER TABLE ONLY registros_ocupacao
    ADD CONSTRAINT registros_ocupacao_registrado_por_id_fkey FOREIGN KEY (registrado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY reservas
    ADD CONSTRAINT reservas_avaliada_por_id_fkey FOREIGN KEY (avaliada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY reservas
    ADD CONSTRAINT reservas_espaco_id_fkey FOREIGN KEY (espaco_id) REFERENCES espacos_comuns(id) ON DELETE CASCADE;

ALTER TABLE ONLY reservas
    ADD CONSTRAINT reservas_morador_id_fkey FOREIGN KEY (morador_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY unidades
    ADD CONSTRAINT unidades_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY usuarios
    ADD CONSTRAINT usuarios_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE SET NULL;

ALTER TABLE ONLY usuarios
    ADD CONSTRAINT usuarios_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_confirmado_por_id_fkey FOREIGN KEY (confirmado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_registrado_por_id_fkey FOREIGN KEY (registrado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;


-- ───────────────────────────────────────────────────────────────────
-- 5. ÍNDICES
-- Acompanham as colunas mais usadas em filtros e junções.
-- ───────────────────────────────────────────────────────────────────

CREATE INDEX ix_cobrancas_competencia ON cobrancas USING btree (competencia);

CREATE INDEX ix_cobrancas_status ON cobrancas USING btree (status);

CREATE INDEX ix_cobrancas_unidade_id ON cobrancas USING btree (unidade_id);

CREATE INDEX ix_cobrancas_vencimento ON cobrancas USING btree (vencimento);

CREATE INDEX ix_codigos_verificacao_usuario_id ON codigos_verificacao USING btree (usuario_id);

CREATE INDEX ix_comunicados_autor_id ON comunicados USING btree (autor_id);

CREATE INDEX ix_comunicados_categoria ON comunicados USING btree (categoria);

CREATE INDEX ix_comunicados_condominio_id ON comunicados USING btree (condominio_id);

CREATE INDEX ix_comunicados_publicado_em ON comunicados USING btree (publicado_em);

CREATE INDEX ix_condominios_sindico_id ON condominios USING btree (sindico_id);

CREATE INDEX ix_encomendas_codigo_rastreio ON encomendas USING btree (codigo_rastreio);

CREATE INDEX ix_encomendas_registrada_por_id ON encomendas USING btree (registrada_por_id);

CREATE INDEX ix_encomendas_status ON encomendas USING btree (status);

CREATE INDEX ix_encomendas_unidade_id ON encomendas USING btree (unidade_id);

CREATE INDEX ix_espacos_comuns_condominio_id ON espacos_comuns USING btree (condominio_id);

CREATE INDEX ix_leituras_comunicado_comunicado_id ON leituras_comunicado USING btree (comunicado_id);

CREATE INDEX ix_leituras_comunicado_usuario_id ON leituras_comunicado USING btree (usuario_id);

CREATE INDEX ix_ocorrencias_aberta_por_id ON ocorrencias USING btree (aberta_por_id);

CREATE INDEX ix_ocorrencias_condominio_id ON ocorrencias USING btree (condominio_id);

CREATE INDEX ix_ocorrencias_status ON ocorrencias USING btree (status);

CREATE INDEX ix_ocorrencias_unidade_id ON ocorrencias USING btree (unidade_id);

CREATE INDEX ix_pagamentos_cobranca_id ON pagamentos USING btree (cobranca_id);

CREATE INDEX ix_pagamentos_pago_por_id ON pagamentos USING btree (pago_por_id);

CREATE INDEX ix_registros_ocupacao_espaco_id ON registros_ocupacao USING btree (espaco_id);

CREATE INDEX ix_registros_ocupacao_registrado_em ON registros_ocupacao USING btree (registrado_em);

CREATE INDEX ix_reservas_data ON reservas USING btree (data);

CREATE INDEX ix_reservas_espaco_id ON reservas USING btree (espaco_id);

CREATE INDEX ix_reservas_morador_id ON reservas USING btree (morador_id);

CREATE INDEX ix_reservas_status ON reservas USING btree (status);

CREATE INDEX ix_unidades_condominio_id ON unidades USING btree (condominio_id);

CREATE INDEX ix_usuarios_condominio_id ON usuarios USING btree (condominio_id);

CREATE INDEX ix_usuarios_unidade_id ON usuarios USING btree (unidade_id);

CREATE INDEX ix_visitantes_registrado_por_id ON visitantes USING btree (registrado_por_id);

CREATE INDEX ix_visitantes_status ON visitantes USING btree (status);

CREATE INDEX ix_visitantes_unidade_id ON visitantes USING btree (unidade_id);

CREATE UNIQUE INDEX ix_condominios_cnpj ON condominios USING btree (cnpj);

CREATE UNIQUE INDEX ix_condominios_codigo_acesso ON condominios USING btree (codigo_acesso);

CREATE UNIQUE INDEX ix_permissoes_porteiro_porteiro_id ON permissoes_porteiro USING btree (porteiro_id);

CREATE UNIQUE INDEX ix_preferencias_cobranca_morador_id ON preferencias_cobranca USING btree (morador_id);

CREATE UNIQUE INDEX ix_usuarios_cpf ON usuarios USING btree (cpf);

CREATE UNIQUE INDEX ix_usuarios_email ON usuarios USING btree (email);


-- ═══════════════════════════════════════════════════════════════════
-- Fim. Confira as tabelas criadas com:
--
--   SELECT tablename FROM pg_tables
--    WHERE schemaname = 'public'
--    ORDER BY tablename;
--
-- Em seguida, execute 02_carga_dados.sql.
-- ═══════════════════════════════════════════════════════════════════
