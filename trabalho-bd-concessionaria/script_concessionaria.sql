-- =============================================================
-- BANCO DE DADOS DE UMA CONCESSIONÁRIA DE VEÍCULOS
-- SGBD: MySQL 8.0 (motor de armazenamento InnoDB)
--
-- Execute o arquivo inteiro, de cima para baixo:
--   MySQL Workbench: abrir o arquivo e usar Ctrl+Shift+Enter
--   Terminal:        mysql -u root -p < script_concessionaria.sql
-- =============================================================

SET NAMES utf8mb4;

-- -------------------------------------------------------------
-- 1) CRIAÇÃO DO BANCO DE DADOS
-- -------------------------------------------------------------

-- Apaga uma versão anterior para que o script possa ser executado
-- novamente sem erro
DROP DATABASE IF EXISTS concessionaria_db;

CREATE DATABASE concessionaria_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE concessionaria_db;

-- -------------------------------------------------------------
-- 2) CRIAÇÃO DA ESTRUTURA DE TABELAS (DDL)
--    As tabelas referenciadas são criadas antes das que as
--    referenciam por chave estrangeira.
-- -------------------------------------------------------------

CREATE TABLE fornecedores (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    nome     VARCHAR(100) NOT NULL,
    cnpj     VARCHAR(18)  NOT NULL,
    telefone VARCHAR(15),
    CONSTRAINT uq_fornecedor_cnpj UNIQUE (cnpj)
) ENGINE = InnoDB;

CREATE TABLE veiculos (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    marca         VARCHAR(50)   NOT NULL,
    modelo        VARCHAR(50)   NOT NULL,
    ano           YEAR          NOT NULL,
    cor           VARCHAR(30),
    placa         VARCHAR(8),
    preco         DECIMAL(10,2) NOT NULL,
    status        VARCHAR(20)   NOT NULL DEFAULT 'Disponivel',
    fornecedor_id INT,
    CONSTRAINT uq_veiculo_placa UNIQUE (placa),
    CONSTRAINT ck_veiculo_preco CHECK (preco > 0),
    CONSTRAINT ck_veiculo_status
        CHECK (status IN ('Disponivel', 'Reservado', 'Vendido')),
    CONSTRAINT fk_veiculo_fornecedor
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE = InnoDB;

CREATE TABLE clientes (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    nome     VARCHAR(100) NOT NULL,
    cpf      VARCHAR(14)  NOT NULL,
    telefone VARCHAR(15),
    email    VARCHAR(100),
    endereco VARCHAR(150),
    CONSTRAINT uq_cliente_cpf UNIQUE (cpf)
) ENGINE = InnoDB;

CREATE TABLE funcionarios (
    id       INT           AUTO_INCREMENT PRIMARY KEY,
    nome     VARCHAR(100)  NOT NULL,
    cargo    VARCHAR(50)   NOT NULL,
    salario  DECIMAL(10,2) NOT NULL,
    telefone VARCHAR(15),
    CONSTRAINT ck_funcionario_salario CHECK (salario > 0)
) ENGINE = InnoDB;

CREATE TABLE vendas (
    id             INT           AUTO_INCREMENT PRIMARY KEY,
    cliente_id     INT           NOT NULL,
    funcionario_id INT           NOT NULL,
    veiculo_id     INT           NOT NULL,
    data_venda     DATE          NOT NULL,
    valor_venda    DECIMAL(10,2) NOT NULL,
    CONSTRAINT uq_venda_veiculo UNIQUE (veiculo_id),
    CONSTRAINT ck_venda_valor CHECK (valor_venda > 0),
    CONSTRAINT fk_venda_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_venda_funcionario
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_venda_veiculo
        FOREIGN KEY (veiculo_id) REFERENCES veiculos (id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -------------------------------------------------------------
-- 3) CARGA DE DADOS (DML)
-- -------------------------------------------------------------

-- 3.1) INSERT: cadastros iniciais (dados fictícios)

INSERT INTO fornecedores (nome, cnpj, telefone) VALUES
    ('Auto Distribuidora Sul',        '12.345.678/0001-90', '(67) 3321-1122'),
    ('Veículos Brasil Ltda',          '98.765.432/0001-10', '(11) 4002-8922'),
    ('Centro-Oeste Automotores S.A.', '45.678.912/0001-33', '(67) 3025-4455');

-- A coluna status não é informada: recebe o valor padrão 'Disponivel'.
-- O Kwid é 0 km e ainda não foi emplacado, por isso a placa fica NULL.
INSERT INTO veiculos
    (marca, modelo, ano, cor, placa, preco, fornecedor_id)
VALUES
    ('Volkswagen', 'Gol',     2023, 'Branco',   'ABC1D23',  78900.00, 1),
    ('Chevrolet',  'Onix',    2024, 'Prata',    'DEF4E56',  85500.00, 1),
    ('Fiat',       'Toro',    2023, 'Vermelho', 'GHI7F89', 129900.00, 2),
    ('Toyota',     'Corolla', 2024, 'Preto',    'JKL0G12', 145000.00, 2),
    ('Hyundai',    'HB20',    2025, 'Cinza',    'MNO3H45',  92900.00, 3),
    ('Jeep',       'Compass', 2025, 'Branco',   'PQR6I78', 189900.00, 3),
    ('Renault',    'Kwid',    2026, 'Laranja',  NULL,       74990.00, 1);

INSERT INTO clientes (nome, cpf, telefone, email, endereco) VALUES
    ('Mariana Souza', '123.456.789-00', '(67) 99911-2233',
     'mariana.souza@email.com', 'Rua das Flores, 120 - Campo Grande/MS'),
    ('Ricardo Alves', '987.654.321-00', '(67) 98822-3344',
     'ricardo.alves@email.com', 'Av. Afonso Pena, 500 - Campo Grande/MS'),
    ('Fernanda Oliveira', '456.789.123-00', '(67) 99155-4466',
     'fernanda.oliveira@email.com', 'Rua 14 de Julho, 1800 - Campo Grande/MS'),
    ('Paulo Henrique Costa', '741.852.963-00', '(67) 98431-7788',
     'paulo.costa@email.com', 'Rua Hayel Bon Faker, 950 - Dourados/MS');

INSERT INTO funcionarios (nome, cargo, salario, telefone) VALUES
    ('Bruno Lima',       'Vendedor',          2500.00, '(67) 99777-1111'),
    ('Camila Fernandes', 'Gerente de Vendas', 5200.00, '(67) 99666-2222'),
    ('Diego Rocha',      'Vendedor',          2500.00, '(67) 99555-3333');

-- 3.2) INSERT + UPDATE: registro das vendas
-- Cada venda grava a linha em vendas e marca o veículo como vendido.
-- As duas operações ficam na mesma transação: ou as duas são
-- gravadas, ou nenhuma é.

START TRANSACTION;
INSERT INTO vendas
    (cliente_id, funcionario_id, veiculo_id, data_venda, valor_venda)
VALUES (1, 1, 1, '2026-09-15', 77500.00);
UPDATE veiculos SET status = 'Vendido' WHERE id = 1;
COMMIT;

START TRANSACTION;
INSERT INTO vendas
    (cliente_id, funcionario_id, veiculo_id, data_venda, valor_venda)
VALUES (3, 3, 4, '2026-09-17', 142000.00);
UPDATE veiculos SET status = 'Vendido' WHERE id = 4;
COMMIT;

START TRANSACTION;
INSERT INTO vendas
    (cliente_id, funcionario_id, veiculo_id, data_venda, valor_venda)
VALUES (4, 1, 5, '2026-09-19', 91500.00);
UPDATE veiculos SET status = 'Vendido' WHERE id = 5;
COMMIT;

-- 3.3) UPDATE: atualização de dados

-- Reajuste de preço de um veículo específico
UPDATE veiculos
SET preco = 89900.00
WHERE modelo = 'Onix';

-- Reserva de um veículo para um cliente
UPDATE veiculos
SET status = 'Reservado'
WHERE placa = 'PQR6I78';

-- Atualização do telefone de um cliente
UPDATE clientes
SET telefone = '(67) 99911-9999'
WHERE cpf = '123.456.789-00';

-- Reajuste salarial de 5% para todos os vendedores
UPDATE funcionarios
SET salario = salario * 1.05
WHERE cargo = 'Vendedor';

-- 3.4) DELETE: remoção de dados

-- Remove um veículo que não foi vendido (devolvido ao fornecedor)
DELETE FROM veiculos
WHERE placa = 'DEF4E56';

-- Remove um cliente que nunca realizou compras
DELETE FROM clientes
WHERE cpf = '987.654.321-00';

-- -------------------------------------------------------------
-- 4) TESTES DE INTEGRIDADE
--    Os comandos abaixo DEVEM falhar: é o SGBD protegendo os dados.
--    Estão comentados para não interromper o script; para testar,
--    retire o "-- " do início das linhas e execute só aquele comando.
-- -------------------------------------------------------------

-- a) Excluir um cliente que já comprou (bloqueado pela chave estrangeira)
-- DELETE FROM clientes WHERE cpf = '123.456.789-00';

-- b) Vender de novo um veículo já vendido (bloqueado pelo UNIQUE)
-- INSERT INTO vendas
--     (cliente_id, funcionario_id, veiculo_id, data_venda, valor_venda)
-- VALUES (3, 3, 1, '2026-09-21', 70000.00);

-- c) Gravar uma situação inexistente (bloqueado pelo CHECK)
-- UPDATE veiculos SET status = 'Vendida' WHERE id = 6;

-- -------------------------------------------------------------
-- 5) CONSULTAS DE VERIFICAÇÃO
-- -------------------------------------------------------------

-- Quantidade de registros em cada tabela
SELECT 'fornecedores' AS tabela, COUNT(*) AS registros FROM fornecedores
UNION ALL SELECT 'veiculos',     COUNT(*) FROM veiculos
UNION ALL SELECT 'clientes',     COUNT(*) FROM clientes
UNION ALL SELECT 'funcionarios', COUNT(*) FROM funcionarios
UNION ALL SELECT 'vendas',       COUNT(*) FROM vendas;

-- Veículos em estoque (não vendidos), com o nome do fornecedor
SELECT v.marca, v.modelo, v.ano, v.preco, v.status,
       f.nome AS fornecedor
FROM veiculos v
LEFT JOIN fornecedores f ON f.id = v.fornecedor_id
WHERE v.status <> 'Vendido'
ORDER BY v.preco;

-- Vendas com o nome do cliente, do funcionário e o veículo vendido
SELECT vd.id, c.nome AS cliente, fu.nome AS funcionario,
       CONCAT(ve.marca, ' ', ve.modelo) AS veiculo,
       vd.data_venda, vd.valor_venda
FROM vendas vd
JOIN clientes c      ON c.id  = vd.cliente_id
JOIN funcionarios fu ON fu.id = vd.funcionario_id
JOIN veiculos ve     ON ve.id = vd.veiculo_id
ORDER BY vd.data_venda;

-- Total vendido por funcionário
SELECT fu.nome, fu.cargo,
       COUNT(vd.id) AS vendas,
       COALESCE(SUM(vd.valor_venda), 0) AS total_vendido
FROM funcionarios fu
LEFT JOIN vendas vd ON vd.funcionario_id = fu.id
GROUP BY fu.id, fu.nome, fu.cargo
ORDER BY total_vendido DESC;
