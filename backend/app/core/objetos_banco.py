"""Objetos programáveis do banco: visões, funções, procedimentos, gatilhos,
o índice parcial das cobranças em aberto e a tabela de log das cobranças.

O mesmo SQL de banco/04_programacao.sql: REMOVER é o cabeçalho do script,
que apaga o que existir, e CRIAR é o resto. A migração instala os objetos
no banco do sistema e os testes rodam com os gatilhos ligados. Os
gatilhos repetem, no banco, regras que a API já confere — não pagar
cobrança cancelada ou negociada, não pagar além do que falta —, para
valerem também para quem gravar direto no banco.

Executar pelo driver, sem parâmetros: o texto tem % dos RAISE.
"""

REMOVER = r"""DROP VIEW IF EXISTS vw_situacao_unidades, vw_balancete_mensal, vw_moradores;
DROP PROCEDURE IF EXISTS sp_gerar_taxa_mensal, sp_registrar_pagamento;
DROP FUNCTION IF EXISTS fn_valida_pagamento, fn_quita_cobranca, fn_log_cobranca, fn_atualizado_em CASCADE;
DROP FUNCTION IF EXISTS fn_rateio, fn_encargos, fn_total_pago;
DROP TABLE IF EXISTS log_cobrancas;
DROP INDEX IF EXISTS ix_cobrancas_em_aberto;
"""

CRIAR = r"""CREATE TABLE log_cobrancas (
    id serial PRIMARY KEY,
    cobranca_id integer NOT NULL REFERENCES cobrancas (id),
    status_anterior varchar(20),
    status_novo varchar(20),
    valor_anterior numeric(10,2),
    valor_novo numeric(10,2),
    vencimento_anterior date,
    vencimento_novo date,
    usuario_banco varchar(63) NOT NULL DEFAULT current_user,
    alterado_em timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX ix_cobrancas_em_aberto
    ON cobrancas (vencimento)
 WHERE status IN ('ABERTA', 'VENCIDA');

CREATE FUNCTION fn_total_pago(p_cobranca integer)
RETURNS numeric
LANGUAGE sql STABLE
AS $$
    SELECT COALESCE(SUM(valor - encargos), 0)
      FROM pagamentos
     WHERE cobranca_id = p_cobranca;
$$;

CREATE FUNCTION fn_encargos(p_cobranca integer, p_dia date DEFAULT CURRENT_DATE)
RETURNS TABLE (dias_atraso integer, multa numeric, juros numeric, total numeric)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    v_status status_cobranca;
    v_restante numeric;
    v_vencimento date;
    v_multa_pct numeric;
    v_juros_pct numeric;
BEGIN
    SELECT c.status, c.valor - fn_total_pago(c.id), c.vencimento, co.multa_atraso, co.juros_mensais
      INTO v_status, v_restante, v_vencimento, v_multa_pct, v_juros_pct
      FROM cobrancas c
      JOIN unidades u ON u.id = c.unidade_id
      JOIN condominios co ON co.id = u.condominio_id
     WHERE c.id = p_cobranca;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'A cobrança % não existe.', p_cobranca;
    END IF;

    dias_atraso := GREATEST(p_dia - v_vencimento, 0);
    IF dias_atraso = 0 OR v_restante <= 0 OR v_status NOT IN ('ABERTA', 'VENCIDA') THEN
        dias_atraso := 0;
        multa := 0.00;
        juros := 0.00;
    ELSE
        multa := ROUND(v_restante * v_multa_pct / 100, 2);
        juros := ROUND(v_restante * v_juros_pct / 100 * dias_atraso / 30, 2);
    END IF;
    total := multa + juros;
    RETURN NEXT;
END;
$$;

CREATE FUNCTION fn_rateio(p_condominio integer, p_total numeric)
RETURNS TABLE (unidade_id integer, apartamento varchar, fracao numeric, valor numeric)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    v_faltam integer;
    v_soma numeric;
BEGIN
    IF p_total IS NULL OR p_total <= 0 THEN
        RAISE EXCEPTION 'O total a ratear precisa ser maior que zero.';
    END IF;

    SELECT COUNT(*) FILTER (WHERE u.fracao_ideal IS NULL), COALESCE(SUM(u.fracao_ideal), 0)
      INTO v_faltam, v_soma
      FROM unidades u
     WHERE u.condominio_id = p_condominio
       AND NOT u.pendente;

    IF v_faltam > 0 THEN
        RAISE EXCEPTION 'Faltam as frações ideais de % unidade(s).', v_faltam;
    END IF;
    IF ABS(v_soma - 100) > 0.01 THEN
        RAISE EXCEPTION 'As frações ideais somam %; precisam somar 100%%.', trim_scale(v_soma) || '%';
    END IF;

    RETURN QUERY
    WITH base AS (
        SELECT u.id, u.bloco, u.numero, u.fracao_ideal,
               p_total * 100 * u.fracao_ideal / v_soma AS exato
          FROM unidades u
         WHERE u.condominio_id = p_condominio
           AND NOT u.pendente
    ),
    piso AS (
        SELECT b.*, floor(b.exato) AS centavos, b.exato - floor(b.exato) AS resto
          FROM base b
    ),
    sobra AS (
        SELECT round(p_total * 100) - SUM(p.centavos) AS n
          FROM piso p
    )
    SELECT p.id, p.numero, p.fracao_ideal,
           ((p.centavos + CASE WHEN ROW_NUMBER() OVER (ORDER BY p.resto DESC, p.id) <= s.n
                               THEN 1 ELSE 0 END) / 100)::numeric(10,2)
      FROM piso p
     CROSS JOIN sobra s
     ORDER BY p.bloco, p.numero;
END;
$$;

CREATE PROCEDURE sp_gerar_taxa_mensal(
    p_condominio integer,
    p_competencia date,
    p_valor numeric,
    p_por_fracao boolean DEFAULT false,
    p_dia_vencimento integer DEFAULT 10,
    INOUT geradas integer DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_mes date := date_trunc('month', p_competencia)::date;
    v_vencimento date;
BEGIN
    IF p_valor IS NULL OR p_valor <= 0 THEN
        RAISE EXCEPTION 'O valor da taxa precisa ser maior que zero.';
    END IF;
    IF p_dia_vencimento NOT BETWEEN 1 AND 28 THEN
        RAISE EXCEPTION 'O dia do vencimento vai de 1 a 28.';
    END IF;
    v_vencimento := v_mes + (p_dia_vencimento - 1);

    INSERT INTO cobrancas (unidade_id, competencia, descricao, valor, vencimento, status, origem)
    SELECT u.id,
           v_mes,
           'Taxa de condomínio ' || to_char(v_mes, 'MM/YYYY'),
           CASE WHEN p_por_fracao THEN r.valor ELSE p_valor END,
           v_vencimento,
           CASE WHEN v_vencimento < CURRENT_DATE THEN 'VENCIDA' ELSE 'ABERTA' END::status_cobranca,
           'TAXA'
      FROM unidades u
      LEFT JOIN fn_rateio(p_condominio, CASE WHEN p_por_fracao THEN p_valor END) r
             ON p_por_fracao AND r.unidade_id = u.id
     WHERE u.condominio_id = p_condominio
       AND NOT u.pendente
       AND NOT EXISTS (
             SELECT 1
               FROM cobrancas c
              WHERE c.unidade_id = u.id
                AND c.competencia = v_mes
                AND c.origem = 'TAXA'
                AND c.status <> 'CANCELADA'
           );

    GET DIAGNOSTICS geradas = ROW_COUNT;
    RAISE NOTICE '% cobrança(s) gerada(s) para %.', geradas, to_char(v_mes, 'MM/YYYY');
END;
$$;

CREATE PROCEDURE sp_registrar_pagamento(
    p_cobranca integer,
    p_forma forma_pagamento,
    p_pago_por integer,
    p_valor numeric DEFAULT NULL,
    INOUT pagamento_id integer DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_restante numeric;
    v_encargos numeric;
    v_valor numeric;
BEGIN
    SELECT c.valor - fn_total_pago(c.id)
      INTO v_restante
      FROM cobrancas c
     WHERE c.id = p_cobranca
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'A cobrança % não existe.', p_cobranca;
    END IF;

    SELECT e.total INTO v_encargos FROM fn_encargos(p_cobranca) e;
    v_valor := COALESCE(p_valor, v_restante + v_encargos);
    IF v_valor <= 0 THEN
        RAISE EXCEPTION 'O valor do pagamento precisa ser maior que zero.';
    END IF;

    INSERT INTO pagamentos (cobranca_id, pago_por_id, valor, encargos, forma, pago_em)
    VALUES (p_cobranca, p_pago_por, v_valor, LEAST(v_valor, v_encargos), p_forma, now())
    RETURNING id INTO pagamento_id;

    RAISE NOTICE 'Pagamento % registrado: % (sendo % de multa e juros).',
                 pagamento_id, v_valor, LEAST(v_valor, v_encargos);
END;
$$;

CREATE FUNCTION fn_valida_pagamento()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_status status_cobranca;
    v_valor numeric;
    v_falta numeric;
BEGIN
    SELECT status, valor INTO v_status, v_valor
      FROM cobrancas
     WHERE id = NEW.cobranca_id
       FOR UPDATE;

    IF v_status IN ('CANCELADA', 'NEGOCIADA') THEN
        RAISE EXCEPTION 'A cobrança % está %: não recebe pagamento.',
                        NEW.cobranca_id, lower(v_status::text);
    END IF;

    v_falta := v_valor - fn_total_pago(NEW.cobranca_id);
    IF NEW.valor - NEW.encargos > v_falta THEN
        RAISE EXCEPTION 'O pagamento abate %, mas da cobrança % só falta %.',
                        NEW.valor - NEW.encargos, NEW.cobranca_id, v_falta;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_valida_pagamento
BEFORE INSERT ON pagamentos
FOR EACH ROW EXECUTE FUNCTION fn_valida_pagamento();

CREATE FUNCTION fn_quita_cobranca()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE cobrancas
       SET status = 'PAGA'
     WHERE id = NEW.cobranca_id
       AND status IN ('ABERTA', 'VENCIDA')
       AND fn_total_pago(id) >= valor;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_quita_cobranca
AFTER INSERT ON pagamentos
FOR EACH ROW EXECUTE FUNCTION fn_quita_cobranca();

CREATE FUNCTION fn_log_cobranca()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO log_cobrancas (cobranca_id, status_anterior, status_novo,
                               valor_anterior, valor_novo,
                               vencimento_anterior, vencimento_novo)
    VALUES (NEW.id, OLD.status, NEW.status,
            OLD.valor, NEW.valor,
            OLD.vencimento, NEW.vencimento);
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_log_cobranca
AFTER UPDATE ON cobrancas
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status
   OR OLD.valor IS DISTINCT FROM NEW.valor
   OR OLD.vencimento IS DISTINCT FROM NEW.vencimento)
EXECUTE FUNCTION fn_log_cobranca();

CREATE FUNCTION fn_atualizado_em()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_atualizado_em BEFORE UPDATE ON cobrancas
FOR EACH ROW EXECUTE FUNCTION fn_atualizado_em();

CREATE TRIGGER trg_atualizado_em BEFORE UPDATE ON unidades
FOR EACH ROW EXECUTE FUNCTION fn_atualizado_em();

CREATE TRIGGER trg_atualizado_em BEFORE UPDATE ON reservas
FOR EACH ROW EXECUTE FUNCTION fn_atualizado_em();

CREATE VIEW vw_situacao_unidades AS
SELECT u.id AS unidade_id,
       u.numero AS apartamento,
       u.fracao_ideal,
       (SELECT m.nome
          FROM usuarios m
         WHERE m.unidade_id = u.id
           AND m.papel = 'MORADOR'
           AND m.status = 'ATIVO'
         ORDER BY m.reside DESC, m.tipo_ocupacao, m.id
         LIMIT 1) AS responsavel,
       COUNT(c.id) FILTER (WHERE c.status IN ('ABERTA', 'VENCIDA')
                             AND c.vencimento < CURRENT_DATE) AS cobrancas_em_atraso,
       COALESCE(SUM(c.valor - COALESCE(p.pago, 0))
                FILTER (WHERE c.status IN ('ABERTA', 'VENCIDA')
                          AND c.vencimento < CURRENT_DATE), 0) AS valor_em_atraso,
       COALESCE(SUM(c.valor - COALESCE(p.pago, 0))
                FILTER (WHERE c.status IN ('ABERTA', 'VENCIDA')
                          AND c.vencimento >= CURRENT_DATE), 0) AS a_vencer,
       CASE WHEN COUNT(c.id) FILTER (WHERE c.status IN ('ABERTA', 'VENCIDA')
                                       AND c.vencimento < CURRENT_DATE) > 0
            THEN 'INADIMPLENTE'
            ELSE 'EM DIA'
       END AS situacao
  FROM unidades u
  LEFT JOIN cobrancas c ON c.unidade_id = u.id
  LEFT JOIN (SELECT cobranca_id, SUM(valor - encargos) AS pago
               FROM pagamentos
              GROUP BY cobranca_id) p
         ON p.cobranca_id = c.id
 WHERE NOT u.pendente
 GROUP BY u.id, u.numero, u.fracao_ideal;

CREATE VIEW vw_balancete_mensal AS
WITH receitas AS (
       SELECT u.condominio_id,
              date_trunc('month', p.pago_em AT TIME ZONE 'America/Campo_Grande')::date AS mes,
              SUM(p.valor) AS valor
         FROM pagamentos p
         JOIN cobrancas c ON c.id = p.cobranca_id
         JOIN unidades u ON u.id = c.unidade_id
        GROUP BY 1, 2
     ),
     gastos AS (
       SELECT condominio_id,
              date_trunc('month', data)::date AS mes,
              SUM(valor) AS valor
         FROM despesas
        WHERE inativo_em IS NULL
        GROUP BY 1, 2
     )
SELECT COALESCE(r.condominio_id, g.condominio_id) AS condominio_id,
       COALESCE(r.mes, g.mes) AS mes,
       COALESCE(r.valor, 0) AS receitas,
       COALESCE(g.valor, 0) AS despesas,
       COALESCE(r.valor, 0) - COALESCE(g.valor, 0) AS saldo_do_mes,
       SUM(COALESCE(r.valor, 0) - COALESCE(g.valor, 0))
           OVER (PARTITION BY COALESCE(r.condominio_id, g.condominio_id)
                 ORDER BY COALESCE(r.mes, g.mes)) AS saldo_acumulado
  FROM receitas r
  FULL JOIN gastos g
         ON g.condominio_id = r.condominio_id
        AND g.mes = r.mes;

CREATE VIEW vw_moradores AS
SELECT m.id,
       m.nome,
       u.numero AS apartamento,
       m.tipo_ocupacao,
       m.reside,
       m.status,
       regexp_replace(m.email, '^(.).*(@.*)$', '\1***\2') AS email
  FROM usuarios m
  JOIN unidades u ON u.id = m.unidade_id
 WHERE m.papel = 'MORADOR';
"""
