TRUNCATE
    condominios,
    unidades,
    usuarios,
    permissoes_porteiro,
    codigos_verificacao,
    espacos_comuns,
    reservas,
    registros_ocupacao,
    preferencias_cobranca,
    cobrancas,
    pagamentos,
    comunicados,
    leituras_comunicado,
    visitantes,
    encomendas,
    ocorrencias,
    movimentacoes_veiculo,
    ordens_servico,
    documentos
RESTART IDENTITY CASCADE;

INSERT INTO condominios (id, nome, cnpj, cep, logradouro, numero, complemento, bairro, cidade, uf, telefone, sindico_id, criado_em, atualizado_em, codigo_acesso) VALUES (1, 'Residencial das Palmeiras', '11222333000181', '79000000', 'Rua das Flores', '100', NULL, 'Centro', 'Campo Grande', 'MS', '6733330000', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00', 'PALM-2025');

INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (1, 1, '101', 'unico', 1, 1, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (2, 1, '102', 'unico', 1, 1, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (3, 1, '204', 'unico', 2, 2, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (4, 1, '301', 'unico', 3, 1, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (5, 1, '302', 'unico', 3, 1, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (6, 1, '410', 'unico', 4, 2, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO unidades (id, condominio_id, numero, bloco, andar, vagas_garagem, criado_em, atualizado_em) VALUES (7, 1, '502', 'unico', 5, 2, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (1, 'Administrador SmartCondo', 'admin@smartcondo.com', '01740740262', '67999990000', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'ADMIN', 'ATIVO', NULL, NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (2, 'Roberto Nascimento', 'sindico@smartcondo.com', '01000000028', '67999990001', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'SINDICO', 'ATIVO', 1, NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (3, 'Carlos Pereira', 'porteiro@smartcondo.com', '01246913402', '67999990003', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'PORTEIRO', 'ATIVO', 1, NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (4, 'Renata Moura', 'renata@smartcondo.com', '01493826859', '67999990004', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'PORTEIRO', 'ATIVO', 1, NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (5, 'João Silva', 'morador@smartcondo.com', '01123456704', '67988880001', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'MORADOR', 'ATIVO', 1, 3, 'PROPRIETARIO', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (6, 'Ana Beatriz Rocha', 'ana@smartcondo.com', '01370370156', '67988880002', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'MORADOR', 'ATIVO', 1, 4, 'PROPRIETARIO', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (7, 'Bruno Cardoso', 'bruno@smartcondo.com', '01617283592', '67988880003', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'MORADOR', 'ATIVO', 1, 2, 'INQUILINO', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (8, 'Marina Duarte', 'marina@smartcondo.com', '01864196947', '67988880004', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'MORADOR', 'ATIVO', 1, 6, 'PROPRIETARIO', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO usuarios (id, nome, email, cpf, telefone, data_nascimento, senha_hash, papel, status, condominio_id, unidade_id, tipo_ocupacao, foto_url, criado_em, atualizado_em) VALUES (9, 'Pedro Henrique Lima', 'pedro@smartcondo.com', '02000000045', '67988880005', NULL, '$2b$12$r1rDrvH4Bww13u3RjgL.suUNWAH6qzPweXHthXqjGta2bsjAVK0va', 'MORADOR', 'AGUARDANDO_APROVACAO', 1, 7, 'INQUILINO', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO permissoes_porteiro (id, porteiro_id, registrar_visitantes, registrar_encomendas, registrar_veiculos, registrar_ocorrencias, acessar_financeiro, definidas_por_id, criado_em, atualizado_em) VALUES (1, 3, true, true, true, true, false, 2, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO permissoes_porteiro (id, porteiro_id, registrar_visitantes, registrar_encomendas, registrar_veiculos, registrar_ocorrencias, acessar_financeiro, definidas_por_id, criado_em, atualizado_em) VALUES (2, 4, true, true, false, false, false, 2, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (1, 1, 'Salão de Festas', 'Com cozinha de apoio e som', 80, true, false, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (2, 1, 'Churrasqueira 1', 'Área descoberta', 20, true, false, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (3, 1, 'Churrasqueira 2', 'Área coberta', 20, true, false, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (4, 1, 'Salão de Jogos', 'Sinuca, ping-pong e mesas', 25, true, false, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (5, 1, 'Piscina', 'Adulto e infantil', 60, false, true, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (6, 1, 'Academia', 'Equipamentos completos', 12, false, true, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (7, 1, 'Playground', 'Área infantil coberta', 20, false, true, false, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO espacos_comuns (id, condominio_id, nome, descricao, capacidade, reservavel, uso_livre, em_manutencao, criado_em, atualizado_em) VALUES (8, 1, 'Coworking', 'Em reforma até o fim do mês', 10, true, false, true, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO reservas (id, espaco_id, morador_id, data, hora_inicio, hora_fim, pessoas_estimadas, observacoes, status, avaliada_por_id, avaliada_em, motivo_recusa, criado_em, atualizado_em) VALUES (1, 1, 5, '2026-09-25', '14:00:00', '22:00:00', 50, 'Aniversário de 15 anos', 'APROVADA', 2, '2026-09-21 01:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO reservas (id, espaco_id, morador_id, data, hora_inicio, hora_fim, pessoas_estimadas, observacoes, status, avaliada_por_id, avaliada_em, motivo_recusa, criado_em, atualizado_em) VALUES (2, 3, 6, '2026-10-02', '11:00:00', '18:00:00', 20, NULL, 'PENDENTE', NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO reservas (id, espaco_id, morador_id, data, hora_inicio, hora_fim, pessoas_estimadas, observacoes, status, avaliada_por_id, avaliada_em, motivo_recusa, criado_em, atualizado_em) VALUES (3, 4, 7, '2026-09-23', '19:00:00', '23:00:00', 12, NULL, 'PENDENTE', NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO reservas (id, espaco_id, morador_id, data, hora_inicio, hora_fim, pessoas_estimadas, observacoes, status, avaliada_por_id, avaliada_em, motivo_recusa, criado_em, atualizado_em) VALUES (4, 1, 8, '2026-08-27', '18:00:00', '23:00:00', 60, NULL, 'CONCLUIDA', NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO registros_ocupacao (id, espaco_id, pessoas, registrado_em, registrado_por_id, criado_em, atualizado_em) VALUES (1, 5, 23, '2026-09-21 01:42:00.304198+00', 3, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO registros_ocupacao (id, espaco_id, pessoas, registrado_em, registrado_por_id, criado_em, atualizado_em) VALUES (2, 6, 11, '2026-09-21 01:42:00.304198+00', 3, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO registros_ocupacao (id, espaco_id, pessoas, registrado_em, registrado_por_id, criado_em, atualizado_em) VALUES (3, 7, 0, '2026-09-21 01:42:00.304198+00', 3, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO preferencias_cobranca (id, morador_id, dia_vencimento, forma_preferida, criado_em, atualizado_em) VALUES (1, 5, 20, 'PIX', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO preferencias_cobranca (id, morador_id, dia_vencimento, forma_preferida, criado_em, atualizado_em) VALUES (2, 6, 10, 'BOLETO', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO preferencias_cobranca (id, morador_id, dia_vencimento, forma_preferida, criado_em, atualizado_em) VALUES (3, 7, 5, 'DEBITO_AUTOMATICO', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (1, 1, '2026-07-01', 'Taxa de condomínio 07/2026', 320.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (2, 2, '2026-07-01', 'Taxa de condomínio 07/2026', 320.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (3, 3, '2026-07-01', 'Taxa de condomínio 07/2026', 320.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (4, 4, '2026-07-01', 'Taxa de condomínio 07/2026', 320.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (5, 5, '2026-07-01', 'Taxa de condomínio 07/2026', 320.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (6, 6, '2026-07-01', 'Taxa de condomínio 07/2026', 410.00, '2026-07-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (7, 1, '2026-08-01', 'Taxa de condomínio 08/2026', 320.00, '2026-08-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (8, 2, '2026-08-01', 'Taxa de condomínio 08/2026', 320.00, '2026-08-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (9, 3, '2026-08-01', 'Taxa de condomínio 08/2026', 320.00, '2026-08-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (10, 4, '2026-08-01', 'Taxa de condomínio 08/2026', 320.00, '2026-08-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (11, 5, '2026-08-01', 'Taxa de condomínio 08/2026', 320.00, '2026-08-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (12, 6, '2026-08-01', 'Taxa de condomínio 08/2026', 410.00, '2026-08-10', 'PAGA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (13, 1, '2026-09-01', 'Taxa de condomínio 09/2026', 320.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (14, 2, '2026-09-01', 'Taxa de condomínio 09/2026', 320.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (15, 3, '2026-09-01', 'Taxa de condomínio 09/2026', 320.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (16, 4, '2026-09-01', 'Taxa de condomínio 09/2026', 320.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (17, 5, '2026-09-01', 'Taxa de condomínio 09/2026', 320.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO cobrancas (id, unidade_id, competencia, descricao, valor, vencimento, status, criado_em, atualizado_em) VALUES (18, 6, '2026-09-01', 'Taxa de condomínio 09/2026', 410.00, '2026-09-10', 'VENCIDA', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (1, 1, NULL, 320.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (2, 2, 7, 320.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (3, 3, 5, 320.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (4, 4, 6, 320.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (5, 5, NULL, 320.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (6, 6, 8, 410.00, 'PIX', '2026-07-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (7, 7, NULL, 320.00, 'PIX', '2026-08-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (8, 8, 7, 320.00, 'PIX', '2026-08-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (9, 9, 5, 320.00, 'PIX', '2026-08-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (10, 10, 6, 320.00, 'PIX', '2026-08-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO pagamentos (id, cobranca_id, pago_por_id, valor, forma, pago_em, comprovante_url, observacao, criado_em, atualizado_em) VALUES (11, 12, 8, 410.00, 'PIX', '2026-08-10 10:30:00+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO comunicados (id, condominio_id, autor_id, titulo, conteudo, categoria, fixado, publicado_em, criado_em, atualizado_em) VALUES (1, 1, 2, 'Manutenção da piscina', 'A piscina ficará fechada no dia 20 para limpeza e troca da bomba. A reabertura está prevista para as 8h do dia seguinte.', 'MANUTENCAO', false, '2026-09-20 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO comunicados (id, condominio_id, autor_id, titulo, conteudo, categoria, fixado, publicado_em, criado_em, atualizado_em) VALUES (2, 1, 2, 'Assembleia geral ordinária', 'Convocamos todos os condôminos para a assembleia no salão de festas, às 19h30. A pauta inclui a prestação de contas e o orçamento do ano.', 'URGENTE', true, '2026-09-18 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO comunicados (id, condominio_id, autor_id, titulo, conteudo, categoria, fixado, publicado_em, criado_em, atualizado_em) VALUES (3, 1, 2, 'Nova regra para a churrasqueira', 'As reservas passam a ser liberadas com até 30 dias de antecedência, por ordem de chegada.', 'GERAL', false, '2026-09-13 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO comunicados (id, condominio_id, autor_id, titulo, conteudo, categoria, fixado, publicado_em, criado_em, atualizado_em) VALUES (4, 1, 2, 'Reforço na portaria', 'A partir deste mês teremos um porteiro adicional no turno da noite.', 'SEGURANCA', false, '2026-09-06 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO comunicados (id, condominio_id, autor_id, titulo, conteudo, categoria, fixado, publicado_em, criado_em, atualizado_em) VALUES (5, 1, 2, 'Reajuste da taxa condominial', 'A taxa passa a R$ 320,00 a partir da próxima competência, conforme aprovado em assembleia.', 'FINANCEIRO', false, '2026-08-30 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO visitantes (id, unidade_id, registrado_por_id, nome, documento, tipo_visita, placa_veiculo, foto_url, status, entrada_em, saida_em, confirmado_por_id, confirmado_em, criado_em, atualizado_em) VALUES (1, 3, 3, 'Marcos Alves', '01864196947', 'Visita pessoal', NULL, NULL, 'AGUARDANDO_CONFIRMACAO', NULL, NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO visitantes (id, unidade_id, registrado_por_id, nome, documento, tipo_visita, placa_veiculo, foto_url, status, entrada_em, saida_em, confirmado_por_id, confirmado_em, criado_em, atualizado_em) VALUES (2, 4, 3, 'Fernanda Souza', '01617283592', 'Visita pessoal', NULL, NULL, 'DENTRO', '2026-09-20 23:45:00.304198+00', NULL, 6, '2026-09-20 23:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO visitantes (id, unidade_id, registrado_por_id, nome, documento, tipo_visita, placa_veiculo, foto_url, status, entrada_em, saida_em, confirmado_por_id, confirmado_em, criado_em, atualizado_em) VALUES (3, 2, 4, 'Lucas Oliveira', '01493826859', 'Prestador de serviço', 'ABC1D23', NULL, 'SAIU', '2026-09-20 19:45:00.304198+00', '2026-09-21 00:45:00.304198+00', 7, '2026-09-20 19:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO encomendas (id, unidade_id, registrada_por_id, remetente, tipo_volume, codigo_rastreio, observacoes, foto_url, status, recebida_em, retirada_em, retirada_por_id, criado_em, atualizado_em) VALUES (1, 3, 3, 'Correios', 'Caixa média', 'BR987654321', NULL, NULL, 'AGUARDANDO_RETIRADA', '2026-09-20 22:45:00.304198+00', NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO encomendas (id, unidade_id, registrada_por_id, remetente, tipo_volume, codigo_rastreio, observacoes, foto_url, status, recebida_em, retirada_em, retirada_por_id, criado_em, atualizado_em) VALUES (2, 4, 4, 'Mercado Livre', 'Envelope / documento', NULL, NULL, NULL, 'RETIRADA', '2026-09-19 01:45:00.304198+00', '2026-09-20 01:45:00.304198+00', 6, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO ocorrencias (id, condominio_id, aberta_por_id, unidade_id, titulo, descricao, categoria, local, prioridade, foto_url, status, resposta, respondida_por_id, respondida_em, criado_em, atualizado_em) VALUES (1, 1, 5, 3, 'Barulho no apartamento vizinho', 'Som alto depois das 23h em dias de semana, por três noites seguidas.', 'convivencia', 'Apto 205', 'ALTA', NULL, 'ABERTA', NULL, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO ocorrencias (id, condominio_id, aberta_por_id, unidade_id, titulo, descricao, categoria, local, prioridade, foto_url, status, resposta, respondida_por_id, respondida_em, criado_em, atualizado_em) VALUES (2, 1, 7, 2, 'Lâmpada queimada na garagem', 'A lâmpada da vaga 12 está queimada há uma semana.', 'manutencao', 'Estacionamento', 'BAIXA', NULL, 'RESOLVIDA', 'Lâmpada trocada pela manutenção.', 2, '2026-09-20 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (1, 1, 'ABC1D23', 'Fiat Argo', 'Prata', 'ENTRADA', 'MORADOR', 3, 3, '2026-09-20 20:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (2, 1, 'DEF2G45', 'Honda Civic', 'Preto', 'ENTRADA', 'MORADOR', 4, 3, '2026-09-20 20:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (3, 1, 'GHI3J67', 'VW Saveiro', 'Branco', 'ENTRADA', 'PRESTADOR', NULL, 3, '2026-09-20 20:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (4, 1, 'JKL4M89', 'Chevrolet Onix', 'Vermelho', 'ENTRADA', 'VISITANTE', NULL, 3, '2026-09-20 20:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (5, 1, 'JKL4M89', 'Chevrolet Onix', 'Vermelho', 'SAIDA', 'VISITANTE', NULL, 3, '2026-09-20 22:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO movimentacoes_veiculo (id, condominio_id, placa, modelo, cor, tipo, categoria, unidade_id, registrada_por_id, registrada_em, observacao, criado_em, atualizado_em) VALUES (6, 1, 'ABC1D23', NULL, NULL, 'SAIDA', 'MORADOR', 3, 3, '2026-09-21 01:45:23.954632+00', NULL, '2026-09-21 01:45:23.948026+00', '2026-09-21 01:45:23.948026+00');

INSERT INTO ordens_servico (id, condominio_id, tipo, descricao, local, prioridade, status, fornecedor, data_prevista, custo_estimado, custo_real, aberta_por_id, concluida_em, observacoes, criado_em, atualizado_em) VALUES (1, 1, 'Elétrica', 'Lâmpadas queimadas na garagem do subsolo.', 'Garagem', 'MEDIA', 'ABERTA', 'Elétrica Silva', '2026-09-28', 450.00, NULL, 2, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO ordens_servico (id, condominio_id, tipo, descricao, local, prioridade, status, fornecedor, data_prevista, custo_estimado, custo_real, aberta_por_id, concluida_em, observacoes, criado_em, atualizado_em) VALUES (2, 1, 'Hidráulica', 'Vazamento na tubulação da churrasqueira.', 'Área de lazer', 'URGENTE', 'EM_ANDAMENTO', 'HidroMS', '2026-09-28', 1200.00, NULL, 2, NULL, NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO ordens_servico (id, condominio_id, tipo, descricao, local, prioridade, status, fornecedor, data_prevista, custo_estimado, custo_real, aberta_por_id, concluida_em, observacoes, criado_em, atualizado_em) VALUES (3, 1, 'Pintura', 'Repintura do hall de entrada.', 'Hall', 'BAIXA', 'CONCLUIDA', 'Pinturas Aurora', NULL, 2800.00, 2650.00, 2, '2026-08-22 01:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO ordens_servico (id, condominio_id, tipo, descricao, local, prioridade, status, fornecedor, data_prevista, custo_estimado, custo_real, aberta_por_id, concluida_em, observacoes, criado_em, atualizado_em) VALUES (4, 1, 'Elevador', 'Manutenção preventiva semestral.', 'Torre A', 'ALTA', 'CONCLUIDA', 'ElevaSul', NULL, 900.00, 900.00, 2, '2026-08-07 01:45:00.304198+00', NULL, '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (1, 1, 'Convenção do Condomínio', 'Documento registrado em cartório.', 'CONVENCAO', 'https://cdn.smartcondo.com/docs/convencao.pdf', 820, NULL, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (2, 1, 'Regimento Interno', 'Regras de convivência e uso das áreas comuns.', 'REGIMENTO', 'https://cdn.smartcondo.com/docs/regimento.pdf', 410, NULL, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (3, 1, 'Ata da Assembleia de Março', 'Prestação de contas e eleição do conselho.', 'ATA', 'https://cdn.smartcondo.com/docs/ata.pdf', 180, NULL, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (4, 1, 'Ata da Assembleia de Janeiro', 'Aprovação do orçamento anual.', 'ATA', 'https://cdn.smartcondo.com/docs/ata.pdf', 165, NULL, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (5, 1, 'Prestação de Contas 2024', 'Balanço completo do exercício.', 'PRESTACAO_CONTAS', 'https://cdn.smartcondo.com/docs/prestacao_contas.pdf', 1240, NULL, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');
INSERT INTO documentos (id, condominio_id, titulo, descricao, categoria, arquivo_url, tamanho_kb, unidade_id, publicado_por_id, publicado_em, criado_em, atualizado_em) VALUES (6, 1, 'Planta Baixa — Apto 204', 'Planta da unidade.', 'PLANTA', 'https://cdn.smartcondo.com/docs/planta.pdf', 2100, 3, 2, '2026-09-11 01:45:00.304198+00', '2026-09-21 01:45:00.611498+00', '2026-09-21 01:45:00.611498+00');

UPDATE condominios SET sindico_id = 2 WHERE id = 1;

SELECT setval('condominios_id_seq', (SELECT COALESCE(MAX(id), 1) FROM condominios));

SELECT setval('unidades_id_seq', (SELECT COALESCE(MAX(id), 1) FROM unidades));

SELECT setval('usuarios_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuarios));

SELECT setval('permissoes_porteiro_id_seq', (SELECT COALESCE(MAX(id), 1) FROM permissoes_porteiro));

SELECT setval('espacos_comuns_id_seq', (SELECT COALESCE(MAX(id), 1) FROM espacos_comuns));

SELECT setval('reservas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM reservas));

SELECT setval('registros_ocupacao_id_seq', (SELECT COALESCE(MAX(id), 1) FROM registros_ocupacao));

SELECT setval('preferencias_cobranca_id_seq', (SELECT COALESCE(MAX(id), 1) FROM preferencias_cobranca));

SELECT setval('cobrancas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM cobrancas));

SELECT setval('pagamentos_id_seq', (SELECT COALESCE(MAX(id), 1) FROM pagamentos));

SELECT setval('comunicados_id_seq', (SELECT COALESCE(MAX(id), 1) FROM comunicados));

SELECT setval('visitantes_id_seq', (SELECT COALESCE(MAX(id), 1) FROM visitantes));

SELECT setval('encomendas_id_seq', (SELECT COALESCE(MAX(id), 1) FROM encomendas));

SELECT setval('ocorrencias_id_seq', (SELECT COALESCE(MAX(id), 1) FROM ocorrencias));

SELECT setval('movimentacoes_veiculo_id_seq', (SELECT COALESCE(MAX(id), 1) FROM movimentacoes_veiculo));

SELECT setval('ordens_servico_id_seq', (SELECT COALESCE(MAX(id), 1) FROM ordens_servico));

SELECT setval('documentos_id_seq', (SELECT COALESCE(MAX(id), 1) FROM documentos));
