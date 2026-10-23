DROP TABLE IF EXISTS
    mudancas,
    veiculos_unidade,
    votos,
    itens_pauta,
    assembleias,
    despesas,
    registros_alteracao,
    documentos_cadastro,
    mensagens,
    documentos,
    ordens_servico,
    movimentacoes_veiculo,
    ocorrencias,
    encomendas,
    visitantes,
    autorizacoes_visita,
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
    usuarios,
    unidades,
    condominios
CASCADE;

DROP TYPE IF EXISTS
    canal_verificacao,
    categoria_comunicado,
    categoria_despesa,
    categoria_documento,
    categoria_veiculo,
    escolha_voto,
    finalidade_codigo,
    maioria_exigida,
    forma_pagamento,
    papel_usuario,
    prioridade_ocorrencia,
    prioridade_ordem_servico,
    status_cobranca,
    status_encomenda,
    status_ocorrencia,
    status_ordem_servico,
    status_mudanca,
    status_reserva,
    status_usuario,
    status_visitante,
    tipo_documento_cadastro,
    tipo_movimentacao,
    tipo_mudanca,
    tipo_ocupacao
CASCADE;

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

CREATE TYPE escolha_voto AS ENUM (
    'A_FAVOR',
    'CONTRA',
    'ABSTENCAO'
);

CREATE TYPE maioria_exigida AS ENUM (
    'SIMPLES',
    'DOIS_TERCOS',
    'UNANIMIDADE'
);

CREATE TYPE categoria_despesa AS ENUM (
    'AGUA',
    'ENERGIA',
    'LIMPEZA',
    'MANUTENCAO',
    'SEGURANCA',
    'PESSOAL',
    'ADMINISTRACAO',
    'OBRAS',
    'OUTROS'
);

CREATE TYPE categoria_documento AS ENUM (
    'CONVENCAO',
    'REGIMENTO',
    'ATA',
    'PLANTA',
    'PRESTACAO_CONTAS',
    'OUTRO'
);

CREATE TYPE categoria_veiculo AS ENUM (
    'MORADOR',
    'VISITANTE',
    'PRESTADOR'
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

CREATE TYPE prioridade_ocorrencia AS ENUM (
    'BAIXA',
    'NORMAL',
    'ALTA',
    'URGENTE'
);

CREATE TYPE prioridade_ordem_servico AS ENUM (
    'BAIXA',
    'MEDIA',
    'ALTA',
    'URGENTE'
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

CREATE TYPE status_ordem_servico AS ENUM (
    'ABERTA',
    'EM_ANDAMENTO',
    'CONCLUIDA',
    'CANCELADA'
);

CREATE TYPE status_mudanca AS ENUM (
    'PENDENTE',
    'APROVADA',
    'RECUSADA',
    'CANCELADA',
    'CONCLUIDA'
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
    'SAIU',
    'SEM_RESPOSTA'
);

CREATE TYPE tipo_documento_cadastro AS ENUM (
    'IDENTIDADE',
    'COMPROVANTE_RESIDENCIA',
    'ESCRITURA'
);

CREATE TYPE tipo_movimentacao AS ENUM (
    'ENTRADA',
    'SAIDA'
);

CREATE TYPE tipo_mudanca AS ENUM (
    'CHEGADA',
    'SAIDA'
);

CREATE TYPE tipo_ocupacao AS ENUM (
    'PROPRIETARIO',
    'INQUILINO',
    'COABITANTE'
);

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
    codigo_acesso character varying(20) NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    -- Multa e juros da cobrança paga com atraso, em %: até 2% e 1% ao mês
    -- (Código Civil, art. 1.336, § 1º).
    multa_atraso numeric(4,2) DEFAULT 2.00 NOT NULL,
    juros_mensais numeric(4,2) DEFAULT 1.00 NOT NULL,
    CONSTRAINT ck_condominio_juros CHECK (((juros_mensais >= (0)::numeric) AND (juros_mensais <= (1)::numeric))),
    CONSTRAINT ck_condominio_multa CHECK (((multa_atraso >= (0)::numeric) AND (multa_atraso <= (2)::numeric)))
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

CREATE TABLE unidades (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    numero character varying(20) NOT NULL,
    bloco character varying(20) NOT NULL,
    andar integer,
    vagas_garagem integer NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    pendente boolean DEFAULT false NOT NULL
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
    avaliado_por_id integer,
    avaliado_em timestamp with time zone,
    motivo_recusa text,
    tentativas_login integer NOT NULL,
    bloqueado_ate timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    versao_sessao integer DEFAULT 0 NOT NULL,
    unidade_desde timestamp with time zone DEFAULT now() NOT NULL,
    reside boolean DEFAULT true NOT NULL,
    conta_principal_id integer
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
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    horario_abertura time without time zone,
    horario_fechamento time without time zone,
    antecedencia_minima_dias integer,
    duracao_maxima_horas integer,
    limite_por_unidade integer,
    CONSTRAINT ck_espaco_horario CHECK ((horario_fechamento > horario_abertura))
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
    cancelada_por_id integer,
    cancelada_em timestamp with time zone,
    motivo_cancelamento text,
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
-- Uma cobrança por unidade e mês, sem contar as canceladas.
CREATE UNIQUE INDEX uq_cobranca_competencia ON cobrancas USING btree (unidade_id, competencia) WHERE (status <> 'CANCELADA'::status_cobranca);

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
    -- Parte do valor que pagou multa e juros do atraso.
    encargos numeric(10,2) DEFAULT 0 NOT NULL,
    CONSTRAINT ck_pagamento_encargos CHECK (((encargos >= (0)::numeric) AND (encargos <= valor))),
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

-- O que o condomínio gastou: a outra metade da prestação de contas
-- (Código Civil, art. 1.348, VIII). A lançada errada é cancelada com
-- motivo (inativo_em) e sai do balancete; nada é apagado.
CREATE TABLE despesas (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    lancada_por_id integer,
    categoria categoria_despesa NOT NULL,
    descricao character varying(180) NOT NULL,
    valor numeric(10,2) NOT NULL,
    data date NOT NULL,
    fornecedor character varying(120),
    comprovante_arquivo character varying(100),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    CONSTRAINT ck_despesa_valor_positivo CHECK ((valor > (0)::numeric))
);
CREATE SEQUENCE despesas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE despesas_id_seq OWNED BY despesas.id;
ALTER TABLE ONLY despesas ALTER COLUMN id SET DEFAULT nextval('despesas_id_seq'::regclass);
ALTER TABLE ONLY despesas
    ADD CONSTRAINT despesas_pkey PRIMARY KEY (id);

-- Assembleia virtual (Código Civil, art. 1.354-A): convocação, pauta e
-- um voto por apartamento em cada item. Cancelar é inativar.
CREATE TABLE assembleias (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    convocada_por_id integer,
    titulo character varying(180) NOT NULL,
    descricao text,
    abre_em timestamp with time zone NOT NULL,
    encerra_em timestamp with time zone NOT NULL,
    motivo_cancelamento character varying(300),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    CONSTRAINT ck_assembleia_periodo CHECK ((encerra_em > abre_em))
);
CREATE SEQUENCE assembleias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE assembleias_id_seq OWNED BY assembleias.id;
ALTER TABLE ONLY assembleias ALTER COLUMN id SET DEFAULT nextval('assembleias_id_seq'::regclass);
ALTER TABLE ONLY assembleias
    ADD CONSTRAINT assembleias_pkey PRIMARY KEY (id);

CREATE TABLE itens_pauta (
    id integer NOT NULL,
    assembleia_id integer NOT NULL,
    ordem integer NOT NULL,
    titulo character varying(180) NOT NULL,
    descricao text,
    maioria maioria_exigida NOT NULL
);
CREATE SEQUENCE itens_pauta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE itens_pauta_id_seq OWNED BY itens_pauta.id;
ALTER TABLE ONLY itens_pauta ALTER COLUMN id SET DEFAULT nextval('itens_pauta_id_seq'::regclass);
ALTER TABLE ONLY itens_pauta
    ADD CONSTRAINT itens_pauta_pkey PRIMARY KEY (id);

CREATE TABLE votos (
    id integer NOT NULL,
    item_id integer NOT NULL,
    unidade_id integer NOT NULL,
    usuario_id integer,
    escolha escolha_voto NOT NULL,
    votado_em timestamp with time zone NOT NULL
);
CREATE SEQUENCE votos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE votos_id_seq OWNED BY votos.id;
ALTER TABLE ONLY votos ALTER COLUMN id SET DEFAULT nextval('votos_id_seq'::regclass);
ALTER TABLE ONLY votos
    ADD CONSTRAINT votos_pkey PRIMARY KEY (id);
ALTER TABLE ONLY votos
    ADD CONSTRAINT uq_voto_por_unidade UNIQUE (item_id, unidade_id);

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
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    -- Para quem: os dois vazios, o condomínio inteiro; ou um bloco, ou um
    -- apartamento (a advertência, que não é da conta dos vizinhos).
    bloco character varying(20),
    unidade_id integer,
    CONSTRAINT ck_comunicado_um_destino CHECK (((bloco IS NULL) OR (unidade_id IS NULL)))
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

CREATE TABLE visitantes (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    registrado_por_id integer,
    nome character varying(160) NOT NULL,
    documento character varying(20) NOT NULL,
    tipo_visita character varying(60) NOT NULL,
    placa_veiculo character varying(10),
    foto_arquivo character varying(100),
    status status_visitante NOT NULL,
    entrada_em timestamp with time zone,
    saida_em timestamp with time zone,
    confirmado_por_id integer,
    confirmado_em timestamp with time zone,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    autorizacao_id integer
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

-- Entrada liberada pelo morador antes de o visitante chegar (diarista,
-- prestador, convidados). Revogar é inativar; nada é apagado.
CREATE TABLE autorizacoes_visita (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    autorizado_por_id integer,
    nome character varying(160) NOT NULL,
    documento character varying(20),
    tipo character varying(60) NOT NULL,
    valida_de date NOT NULL,
    valida_ate date NOT NULL,
    dias_semana character varying(7),
    observacao character varying(300),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer,
    CONSTRAINT ck_autorizacao_periodo CHECK ((valida_ate >= valida_de))
);
CREATE SEQUENCE autorizacoes_visita_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE autorizacoes_visita_id_seq OWNED BY autorizacoes_visita.id;
ALTER TABLE ONLY autorizacoes_visita ALTER COLUMN id SET DEFAULT nextval('autorizacoes_visita_id_seq'::regclass);
ALTER TABLE ONLY autorizacoes_visita
    ADD CONSTRAINT autorizacoes_visita_pkey PRIMARY KEY (id);

CREATE TABLE encomendas (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    registrada_por_id integer,
    remetente character varying(120) NOT NULL,
    tipo_volume character varying(60) NOT NULL,
    codigo_rastreio character varying(60),
    observacoes text,
    foto_arquivo character varying(100),
    status status_encomenda NOT NULL,
    recebida_em timestamp with time zone NOT NULL,
    retirada_em timestamp with time zone,
    retirada_por_id integer,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    entregue_por_id integer,
    retirado_por_nome character varying(120)
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

CREATE TABLE ocorrencias (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    aberta_por_id integer NOT NULL,
    unidade_id integer,
    titulo character varying(180) NOT NULL,
    descricao text NOT NULL,
    categoria character varying(60) NOT NULL,
    local character varying(120),
    prioridade prioridade_ocorrencia NOT NULL,
    foto_arquivo character varying(100),
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

CREATE TABLE movimentacoes_veiculo (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    placa character varying(10) NOT NULL,
    modelo character varying(60),
    cor character varying(30),
    tipo tipo_movimentacao NOT NULL,
    categoria categoria_veiculo NOT NULL,
    unidade_id integer,
    registrada_por_id integer,
    registrada_em timestamp with time zone NOT NULL,
    observacao text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL
);
CREATE SEQUENCE movimentacoes_veiculo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE movimentacoes_veiculo_id_seq OWNED BY movimentacoes_veiculo.id;
ALTER TABLE ONLY movimentacoes_veiculo ALTER COLUMN id SET DEFAULT nextval('movimentacoes_veiculo_id_seq'::regclass);
ALTER TABLE ONLY movimentacoes_veiculo
    ADD CONSTRAINT movimentacoes_veiculo_pkey PRIMARY KEY (id);

-- Placas cadastradas de cada apartamento, para a portaria reconhecer o
-- carro do morador. Uma placa ativa por condomínio; remover é inativar.
CREATE TABLE veiculos_unidade (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    unidade_id integer NOT NULL,
    cadastrado_por_id integer,
    placa character varying(10) NOT NULL,
    modelo character varying(60),
    cor character varying(30),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer
);
CREATE SEQUENCE veiculos_unidade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE veiculos_unidade_id_seq OWNED BY veiculos_unidade.id;
ALTER TABLE ONLY veiculos_unidade ALTER COLUMN id SET DEFAULT nextval('veiculos_unidade_id_seq'::regclass);
ALTER TABLE ONLY veiculos_unidade
    ADD CONSTRAINT veiculos_unidade_pkey PRIMARY KEY (id);

-- Mudanças pedidas pelo morador e avaliadas pelo síndico; a portaria vê
-- as aprovadas. Uma de cada vez em cada bloco (conferido pela API).
CREATE TABLE mudancas (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    unidade_id integer NOT NULL,
    solicitada_por_id integer,
    tipo tipo_mudanca NOT NULL,
    data date NOT NULL,
    hora_inicio time without time zone NOT NULL,
    hora_fim time without time zone NOT NULL,
    empresa character varying(120),
    observacao character varying(300),
    status status_mudanca NOT NULL,
    avaliada_por_id integer,
    avaliada_em timestamp with time zone,
    motivo_recusa character varying(300),
    cancelada_por_id integer,
    cancelada_em timestamp with time zone,
    motivo_cancelamento character varying(300),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_mudanca_intervalo CHECK ((hora_fim > hora_inicio))
);
CREATE SEQUENCE mudancas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE mudancas_id_seq OWNED BY mudancas.id;
ALTER TABLE ONLY mudancas ALTER COLUMN id SET DEFAULT nextval('mudancas_id_seq'::regclass);
ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_pkey PRIMARY KEY (id);

CREATE TABLE ordens_servico (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    tipo character varying(60) NOT NULL,
    descricao text NOT NULL,
    local character varying(120),
    prioridade prioridade_ordem_servico NOT NULL,
    status status_ordem_servico NOT NULL,
    fornecedor character varying(120),
    data_prevista date,
    custo_estimado numeric(10,2),
    custo_real numeric(10,2),
    aberta_por_id integer,
    concluida_em timestamp with time zone,
    observacoes text,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_os_custo_estimado CHECK (((custo_estimado IS NULL) OR (custo_estimado >= (0)::numeric))),
    CONSTRAINT ck_os_custo_real CHECK (((custo_real IS NULL) OR (custo_real >= (0)::numeric)))
);
CREATE SEQUENCE ordens_servico_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE ordens_servico_id_seq OWNED BY ordens_servico.id;
ALTER TABLE ONLY ordens_servico ALTER COLUMN id SET DEFAULT nextval('ordens_servico_id_seq'::regclass);
ALTER TABLE ONLY ordens_servico
    ADD CONSTRAINT ordens_servico_pkey PRIMARY KEY (id);

CREATE TABLE documentos (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    titulo character varying(180) NOT NULL,
    descricao text,
    categoria categoria_documento NOT NULL,
    arquivo character varying(100),
    tipo_conteudo character varying(40),
    tamanho_kb integer,
    unidade_id integer,
    publicado_por_id integer,
    publicado_em timestamp with time zone NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp with time zone DEFAULT now() NOT NULL,
    inativo_em timestamp with time zone,
    inativado_por_id integer
);
CREATE SEQUENCE documentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE documentos_id_seq OWNED BY documentos.id;
ALTER TABLE ONLY documentos ALTER COLUMN id SET DEFAULT nextval('documentos_id_seq'::regclass);
ALTER TABLE ONLY documentos
    ADD CONSTRAINT documentos_pkey PRIMARY KEY (id);

-- Chat entre síndico, porteiros e moradores (seção 13.5.2).
CREATE TABLE mensagens (
    id integer NOT NULL,
    condominio_id integer NOT NULL,
    remetente_id integer NOT NULL,
    destinatario_id integer NOT NULL,
    texto text NOT NULL,
    enviada_em timestamp with time zone DEFAULT now() NOT NULL,
    lida_em timestamp with time zone,
    CONSTRAINT ck_mensagem_para_outra_pessoa CHECK ((remetente_id <> destinatario_id)),
    CONSTRAINT ck_mensagem_tamanho CHECK (((char_length(texto) >= 1) AND (char_length(texto) <= 2000)))
);
CREATE SEQUENCE mensagens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE mensagens_id_seq OWNED BY mensagens.id;
ALTER TABLE ONLY mensagens ALTER COLUMN id SET DEFAULT nextval('mensagens_id_seq'::regclass);
ALTER TABLE ONLY mensagens
    ADD CONSTRAINT mensagens_pkey PRIMARY KEY (id);

-- Documentos enviados pelo morador no cadastro (seção 13.3). O arquivo
-- fica em backend/uploads/documentos; aqui vai só o nome gravado.
CREATE TABLE documentos_cadastro (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo tipo_documento_cadastro NOT NULL,
    arquivo character varying(100) NOT NULL,
    tipo_conteudo character varying(40) NOT NULL,
    tamanho_bytes integer NOT NULL,
    enviado_em timestamp with time zone DEFAULT now() NOT NULL
);
CREATE SEQUENCE documentos_cadastro_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE documentos_cadastro_id_seq OWNED BY documentos_cadastro.id;
ALTER TABLE ONLY documentos_cadastro ALTER COLUMN id SET DEFAULT nextval('documentos_cadastro_id_seq'::regclass);
ALTER TABLE ONLY documentos_cadastro
    ADD CONSTRAINT documentos_cadastro_pkey PRIMARY KEY (id);
ALTER TABLE ONLY documentos_cadastro
    ADD CONSTRAINT uq_documento_cadastro_tipo UNIQUE (usuario_id, tipo);

-- Quem criou, editou, inativou ou reativou cada registro, e quando.
-- Nada é apagado: "excluir" inativa (inativo_em e inativado_por_id em
-- condominios, comunicados e documentos).
CREATE TABLE registros_alteracao (
    id integer NOT NULL,
    autor_id integer,
    acao character varying(20) NOT NULL,
    entidade character varying(30) NOT NULL,
    entidade_id integer NOT NULL,
    descricao text,
    feito_em timestamp with time zone DEFAULT now() NOT NULL
);
CREATE SEQUENCE registros_alteracao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE registros_alteracao_id_seq OWNED BY registros_alteracao.id;
ALTER TABLE ONLY registros_alteracao ALTER COLUMN id SET DEFAULT nextval('registros_alteracao_id_seq'::regclass);
ALTER TABLE ONLY registros_alteracao
    ADD CONSTRAINT registros_alteracao_pkey PRIMARY KEY (id);

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

ALTER TABLE ONLY documentos
    ADD CONSTRAINT documentos_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY documentos
    ADD CONSTRAINT documentos_publicado_por_id_fkey FOREIGN KEY (publicado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY documentos
    ADD CONSTRAINT documentos_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY documentos_cadastro
    ADD CONSTRAINT documentos_cadastro_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY mensagens
    ADD CONSTRAINT mensagens_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY mensagens
    ADD CONSTRAINT mensagens_remetente_id_fkey FOREIGN KEY (remetente_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY mensagens
    ADD CONSTRAINT mensagens_destinatario_id_fkey FOREIGN KEY (destinatario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_registrada_por_id_fkey FOREIGN KEY (registrada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_retirada_por_id_fkey FOREIGN KEY (retirada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_entregue_por_id_fkey FOREIGN KEY (entregue_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY encomendas
    ADD CONSTRAINT encomendas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY espacos_comuns
    ADD CONSTRAINT espacos_comuns_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT leituras_comunicado_comunicado_id_fkey FOREIGN KEY (comunicado_id) REFERENCES comunicados(id) ON DELETE CASCADE;

ALTER TABLE ONLY leituras_comunicado
    ADD CONSTRAINT leituras_comunicado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY movimentacoes_veiculo
    ADD CONSTRAINT movimentacoes_veiculo_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY movimentacoes_veiculo
    ADD CONSTRAINT movimentacoes_veiculo_registrada_por_id_fkey FOREIGN KEY (registrada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY movimentacoes_veiculo
    ADD CONSTRAINT movimentacoes_veiculo_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE SET NULL;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_aberta_por_id_fkey FOREIGN KEY (aberta_por_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_respondida_por_id_fkey FOREIGN KEY (respondida_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY ocorrencias
    ADD CONSTRAINT ocorrencias_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE SET NULL;

ALTER TABLE ONLY ordens_servico
    ADD CONSTRAINT ordens_servico_aberta_por_id_fkey FOREIGN KEY (aberta_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY ordens_servico
    ADD CONSTRAINT ordens_servico_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY assembleias
    ADD CONSTRAINT assembleias_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY assembleias
    ADD CONSTRAINT assembleias_convocada_por_id_fkey FOREIGN KEY (convocada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY assembleias
    ADD CONSTRAINT assembleias_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY itens_pauta
    ADD CONSTRAINT itens_pauta_assembleia_id_fkey FOREIGN KEY (assembleia_id) REFERENCES assembleias(id) ON DELETE CASCADE;

ALTER TABLE ONLY veiculos_unidade
    ADD CONSTRAINT veiculos_unidade_cadastrado_por_id_fkey FOREIGN KEY (cadastrado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY veiculos_unidade
    ADD CONSTRAINT veiculos_unidade_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY veiculos_unidade
    ADD CONSTRAINT veiculos_unidade_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY veiculos_unidade
    ADD CONSTRAINT veiculos_unidade_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_avaliada_por_id_fkey FOREIGN KEY (avaliada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_cancelada_por_id_fkey FOREIGN KEY (cancelada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_solicitada_por_id_fkey FOREIGN KEY (solicitada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY mudancas
    ADD CONSTRAINT mudancas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY votos
    ADD CONSTRAINT votos_item_id_fkey FOREIGN KEY (item_id) REFERENCES itens_pauta(id) ON DELETE CASCADE;

ALTER TABLE ONLY votos
    ADD CONSTRAINT votos_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY votos
    ADD CONSTRAINT votos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY despesas
    ADD CONSTRAINT despesas_condominio_id_fkey FOREIGN KEY (condominio_id) REFERENCES condominios(id) ON DELETE CASCADE;

ALTER TABLE ONLY despesas
    ADD CONSTRAINT despesas_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY despesas
    ADD CONSTRAINT despesas_lancada_por_id_fkey FOREIGN KEY (lancada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

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
    ADD CONSTRAINT reservas_cancelada_por_id_fkey FOREIGN KEY (cancelada_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

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

ALTER TABLE ONLY usuarios
    ADD CONSTRAINT fk_usuarios_avaliado_por_id_usuarios FOREIGN KEY (avaliado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

-- Perfil vinculado (o síndico que também mora, o dono de outro
-- apartamento): aponta para o cadastro com login da mesma pessoa.
ALTER TABLE ONLY usuarios
    ADD CONSTRAINT usuarios_conta_principal_id_fkey FOREIGN KEY (conta_principal_id) REFERENCES usuarios(id) ON DELETE CASCADE;

ALTER TABLE ONLY autorizacoes_visita
    ADD CONSTRAINT autorizacoes_visita_autorizado_por_id_fkey FOREIGN KEY (autorizado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY autorizacoes_visita
    ADD CONSTRAINT autorizacoes_visita_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY autorizacoes_visita
    ADD CONSTRAINT autorizacoes_visita_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY comunicados
    ADD CONSTRAINT comunicados_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_autorizacao_id_fkey FOREIGN KEY (autorizacao_id) REFERENCES autorizacoes_visita(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_confirmado_por_id_fkey FOREIGN KEY (confirmado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_registrado_por_id_fkey FOREIGN KEY (registrado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY visitantes
    ADD CONSTRAINT visitantes_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES unidades(id) ON DELETE CASCADE;

ALTER TABLE ONLY registros_alteracao
    ADD CONSTRAINT registros_alteracao_autor_id_fkey FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY comunicados
    ADD CONSTRAINT comunicados_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY condominios
    ADD CONSTRAINT condominios_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY documentos
    ADD CONSTRAINT documentos_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

ALTER TABLE ONLY espacos_comuns
    ADD CONSTRAINT espacos_comuns_inativado_por_id_fkey FOREIGN KEY (inativado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL;

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

CREATE INDEX ix_documentos_categoria ON documentos USING btree (categoria);

CREATE INDEX ix_documentos_condominio_id ON documentos USING btree (condominio_id);

CREATE INDEX ix_documentos_publicado_em ON documentos USING btree (publicado_em);

CREATE INDEX ix_documentos_publicado_por_id ON documentos USING btree (publicado_por_id);

CREATE INDEX ix_documentos_unidade_id ON documentos USING btree (unidade_id);

CREATE INDEX ix_encomendas_codigo_rastreio ON encomendas USING btree (codigo_rastreio);

CREATE INDEX ix_encomendas_registrada_por_id ON encomendas USING btree (registrada_por_id);

CREATE INDEX ix_encomendas_status ON encomendas USING btree (status);

CREATE INDEX ix_encomendas_unidade_id ON encomendas USING btree (unidade_id);

CREATE INDEX ix_espacos_comuns_condominio_id ON espacos_comuns USING btree (condominio_id);

CREATE INDEX ix_leituras_comunicado_comunicado_id ON leituras_comunicado USING btree (comunicado_id);

CREATE INDEX ix_leituras_comunicado_usuario_id ON leituras_comunicado USING btree (usuario_id);

CREATE INDEX ix_movimentacoes_veiculo_condominio_id ON movimentacoes_veiculo USING btree (condominio_id);

CREATE INDEX ix_movimentacoes_veiculo_placa ON movimentacoes_veiculo USING btree (placa);

CREATE INDEX ix_movimentacoes_veiculo_registrada_em ON movimentacoes_veiculo USING btree (registrada_em);

CREATE INDEX ix_movimentacoes_veiculo_registrada_por_id ON movimentacoes_veiculo USING btree (registrada_por_id);

CREATE INDEX ix_movimentacoes_veiculo_tipo ON movimentacoes_veiculo USING btree (tipo);

CREATE INDEX ix_movimentacoes_veiculo_unidade_id ON movimentacoes_veiculo USING btree (unidade_id);

CREATE INDEX ix_ocorrencias_aberta_por_id ON ocorrencias USING btree (aberta_por_id);

CREATE INDEX ix_ocorrencias_condominio_id ON ocorrencias USING btree (condominio_id);

CREATE INDEX ix_ocorrencias_prioridade ON ocorrencias USING btree (prioridade);

CREATE INDEX ix_ocorrencias_status ON ocorrencias USING btree (status);

CREATE INDEX ix_ocorrencias_unidade_id ON ocorrencias USING btree (unidade_id);

CREATE INDEX ix_ordens_servico_aberta_por_id ON ordens_servico USING btree (aberta_por_id);

CREATE INDEX ix_ordens_servico_condominio_id ON ordens_servico USING btree (condominio_id);

CREATE INDEX ix_ordens_servico_prioridade ON ordens_servico USING btree (prioridade);

CREATE INDEX ix_ordens_servico_status ON ordens_servico USING btree (status);

CREATE INDEX ix_assembleias_condominio_id ON assembleias USING btree (condominio_id);

CREATE INDEX ix_assembleias_convocada_por_id ON assembleias USING btree (convocada_por_id);

CREATE INDEX ix_itens_pauta_assembleia_id ON itens_pauta USING btree (assembleia_id);

CREATE INDEX ix_veiculos_unidade_cadastrado_por_id ON veiculos_unidade USING btree (cadastrado_por_id);

CREATE INDEX ix_veiculos_unidade_condominio_id ON veiculos_unidade USING btree (condominio_id);

CREATE INDEX ix_veiculos_unidade_unidade_id ON veiculos_unidade USING btree (unidade_id);

CREATE UNIQUE INDEX uq_veiculo_placa_ativa ON veiculos_unidade USING btree (condominio_id, placa) WHERE (inativo_em IS NULL);

CREATE INDEX ix_mudancas_condominio_data ON mudancas USING btree (condominio_id, data);

CREATE INDEX ix_mudancas_condominio_id ON mudancas USING btree (condominio_id);

CREATE INDEX ix_mudancas_solicitada_por_id ON mudancas USING btree (solicitada_por_id);

CREATE INDEX ix_mudancas_status ON mudancas USING btree (status);

CREATE INDEX ix_mudancas_unidade_id ON mudancas USING btree (unidade_id);

CREATE INDEX ix_votos_item_id ON votos USING btree (item_id);

CREATE INDEX ix_votos_unidade_id ON votos USING btree (unidade_id);

CREATE INDEX ix_votos_usuario_id ON votos USING btree (usuario_id);

CREATE INDEX ix_despesas_condominio_data ON despesas USING btree (condominio_id, data);

CREATE INDEX ix_despesas_lancada_por_id ON despesas USING btree (lancada_por_id);

CREATE INDEX ix_pagamentos_cobranca_id ON pagamentos USING btree (cobranca_id);

CREATE INDEX ix_pagamentos_pago_por_id ON pagamentos USING btree (pago_por_id);

CREATE INDEX ix_registros_ocupacao_espaco_id ON registros_ocupacao USING btree (espaco_id);

CREATE INDEX ix_registros_ocupacao_registrado_em ON registros_ocupacao USING btree (registrado_em);

CREATE INDEX ix_reservas_data ON reservas USING btree (data);

CREATE INDEX ix_documentos_cadastro_usuario_id ON documentos_cadastro USING btree (usuario_id);

CREATE INDEX ix_mensagens_condominio_id ON mensagens USING btree (condominio_id);

CREATE INDEX ix_mensagens_conversa ON mensagens USING btree (remetente_id, destinatario_id, id);

CREATE INDEX ix_mensagens_nao_lidas ON mensagens USING btree (destinatario_id, lida_em);

CREATE INDEX ix_reservas_espaco_id ON reservas USING btree (espaco_id);

CREATE INDEX ix_reservas_morador_id ON reservas USING btree (morador_id);

CREATE INDEX ix_reservas_status ON reservas USING btree (status);

CREATE INDEX ix_unidades_condominio_id ON unidades USING btree (condominio_id);

CREATE INDEX ix_usuarios_condominio_id ON usuarios USING btree (condominio_id);

CREATE INDEX ix_usuarios_unidade_id ON usuarios USING btree (unidade_id);

CREATE INDEX ix_comunicados_unidade_id ON comunicados USING btree (unidade_id);

CREATE INDEX ix_autorizacoes_visita_autorizado_por_id ON autorizacoes_visita USING btree (autorizado_por_id);

CREATE INDEX ix_autorizacoes_visita_unidade_id ON autorizacoes_visita USING btree (unidade_id);

CREATE INDEX ix_visitantes_autorizacao_id ON visitantes USING btree (autorizacao_id);

CREATE INDEX ix_visitantes_registrado_por_id ON visitantes USING btree (registrado_por_id);

CREATE INDEX ix_visitantes_status ON visitantes USING btree (status);

CREATE INDEX ix_visitantes_unidade_id ON visitantes USING btree (unidade_id);

CREATE UNIQUE INDEX ix_condominios_cnpj ON condominios USING btree (cnpj);

CREATE UNIQUE INDEX ix_condominios_codigo_acesso ON condominios USING btree (codigo_acesso);

CREATE UNIQUE INDEX ix_permissoes_porteiro_porteiro_id ON permissoes_porteiro USING btree (porteiro_id);

CREATE UNIQUE INDEX ix_preferencias_cobranca_morador_id ON preferencias_cobranca USING btree (morador_id);

CREATE INDEX ix_usuarios_cpf ON usuarios USING btree (cpf);

CREATE INDEX ix_usuarios_email ON usuarios USING btree (email);

CREATE INDEX ix_usuarios_conta_principal_id ON usuarios USING btree (conta_principal_id);

-- E-mail e CPF são de uma pessoa só, entre os cadastros com login; os
-- perfis vinculados repetem os dados dela.
CREATE UNIQUE INDEX uq_usuarios_cpf_principal ON usuarios USING btree (cpf) WHERE (conta_principal_id IS NULL);

CREATE UNIQUE INDEX uq_usuarios_email_principal ON usuarios USING btree (email) WHERE (conta_principal_id IS NULL);

CREATE INDEX ix_registros_alteracao_autor_id ON registros_alteracao USING btree (autor_id);

CREATE INDEX ix_registros_alteracao_entidade ON registros_alteracao USING btree (entidade, entidade_id);
