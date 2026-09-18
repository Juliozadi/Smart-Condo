DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS espacos_comuns;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS unidades;
DROP TABLE IF EXISTS condominios;

CREATE TABLE condominios (
    id      SERIAL       PRIMARY KEY,
    nome    VARCHAR(100) NOT NULL,
    cnpj    VARCHAR(18)  NOT NULL UNIQUE,
    cidade  VARCHAR(60)  NOT NULL,
    uf      CHAR(2)      NOT NULL
);

CREATE TABLE unidades (
    id             SERIAL      PRIMARY KEY,
    condominio_id  INTEGER     NOT NULL REFERENCES condominios (id),
    numero         VARCHAR(10) NOT NULL,
    bloco          VARCHAR(10),
    UNIQUE (condominio_id, numero)
);

CREATE TABLE usuarios (
    id             SERIAL       PRIMARY KEY,
    nome           VARCHAR(100) NOT NULL,
    email          VARCHAR(120) NOT NULL UNIQUE,
    senha_hash     VARCHAR(60)  NOT NULL,
    papel          VARCHAR(10)  NOT NULL,
    condominio_id  INTEGER      NOT NULL REFERENCES condominios (id),
    unidade_id     INTEGER      REFERENCES unidades (id),
    CONSTRAINT ck_usuarios_papel
        CHECK (papel IN ('sindico', 'porteiro', 'morador')),
    CONSTRAINT ck_usuarios_unidade_do_morador
        CHECK ((papel = 'morador' AND unidade_id IS NOT NULL)
            OR (papel <> 'morador' AND unidade_id IS NULL))
);

CREATE TABLE espacos_comuns (
    id             SERIAL      PRIMARY KEY,
    condominio_id  INTEGER     NOT NULL REFERENCES condominios (id),
    nome           VARCHAR(60) NOT NULL,
    capacidade     INTEGER     NOT NULL,
    CONSTRAINT ck_espacos_capacidade CHECK (capacidade > 0)
);

CREATE TABLE reservas (
    id           SERIAL      PRIMARY KEY,
    espaco_id    INTEGER     NOT NULL REFERENCES espacos_comuns (id),
    morador_id   INTEGER     NOT NULL REFERENCES usuarios (id),
    data         DATE        NOT NULL,
    hora_inicio  TIME        NOT NULL,
    hora_fim     TIME        NOT NULL,
    status       VARCHAR(10) NOT NULL DEFAULT 'pendente',
    CONSTRAINT ck_reservas_status
        CHECK (status IN ('pendente', 'aprovada', 'recusada')),
    CONSTRAINT ck_reservas_horario CHECK (hora_fim > hora_inicio)
);
