TRUNCATE reservas, espacos_comuns, usuarios, unidades, condominios
    RESTART IDENTITY CASCADE;

INSERT INTO condominios (nome, cnpj, cidade, uf) VALUES
    ('Residencial das Palmeiras', '11.222.333/0001-81', 'Campo Grande', 'MS');

INSERT INTO unidades (condominio_id, numero, bloco) VALUES
    (1, '101', 'A'),
    (1, '102', 'A'),
    (1, '204', 'B'),
    (1, '301', 'B');

INSERT INTO usuarios (nome, email, senha_hash, papel, condominio_id, unidade_id) VALUES
    ('Roberto Nascimento', 'sindico@smartcondo.com',  '$2b$12$099spF2LMrt1Ez50sBIJ9.S3Dp4GqeQscF58G2JTTyOzAWNW4zuqO', 'sindico',  1, NULL),
    ('Carlos Pereira',     'porteiro@smartcondo.com', '$2b$12$099spF2LMrt1Ez50sBIJ9.S3Dp4GqeQscF58G2JTTyOzAWNW4zuqO', 'porteiro', 1, NULL),
    ('Joao Silva',         'joao@smartcondo.com',     '$2b$12$099spF2LMrt1Ez50sBIJ9.S3Dp4GqeQscF58G2JTTyOzAWNW4zuqO', 'morador',  1, 3),
    ('Ana Beatriz Rocha',  'ana@smartcondo.com',      '$2b$12$099spF2LMrt1Ez50sBIJ9.S3Dp4GqeQscF58G2JTTyOzAWNW4zuqO', 'morador',  1, 4),
    ('Bruno Cardoso',      'bruno@smartcondo.com',    '$2b$12$099spF2LMrt1Ez50sBIJ9.S3Dp4GqeQscF58G2JTTyOzAWNW4zuqO', 'morador',  1, 2);

INSERT INTO espacos_comuns (condominio_id, nome, capacidade) VALUES
    (1, 'Salao de Festas', 80),
    (1, 'Churrasqueira',   20),
    (1, 'Piscina',         60),
    (1, 'Academia',        12);

INSERT INTO reservas (espaco_id, morador_id, data, hora_inicio, hora_fim, status) VALUES
    (1, 3, '2025-10-04', '14:00', '22:00', 'aprovada'),
    (2, 4, '2025-10-11', '11:00', '18:00', 'pendente'),
    (1, 5, '2025-10-18', '19:00', '23:00', 'pendente'),
    (3, 3, '2025-09-20', '09:00', '12:00', 'recusada');
