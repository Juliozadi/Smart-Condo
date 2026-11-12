BEGIN;

SELECT * FROM vw_situacao_unidades ORDER BY apartamento;

SELECT to_char(mes, 'MM/YYYY') AS mes, receitas, despesas, saldo_do_mes, saldo_acumulado
  FROM vw_balancete_mensal
 ORDER BY vw_balancete_mensal.mes;

SELECT * FROM fn_rateio(1, 2240.00);

SELECT c.id,
       u.numero AS apartamento,
       c.descricao,
       c.valor,
       e.dias_atraso,
       e.multa,
       e.juros,
       c.valor - fn_total_pago(c.id) + e.total AS total_hoje
  FROM cobrancas c
  JOIN unidades u ON u.id = c.unidade_id
 CROSS JOIN LATERAL fn_encargos(c.id) e
 WHERE c.status IN ('ABERTA', 'VENCIDA')
 ORDER BY u.numero, c.vencimento;

CALL sp_gerar_taxa_mensal(1, (CURRENT_DATE + INTERVAL '1 month')::date, 2240.00, true);

SELECT u.numero AS apartamento, c.descricao, c.valor, c.vencimento, c.status
  FROM cobrancas c
  JOIN unidades u ON u.id = c.unidade_id
 WHERE c.competencia = date_trunc('month', CURRENT_DATE + INTERVAL '1 month')::date
   AND c.origem = 'TAXA'
 ORDER BY u.numero;

CALL sp_gerar_taxa_mensal(1, (CURRENT_DATE + INTERVAL '1 month')::date, 2240.00, true);

CALL sp_registrar_pagamento(13, 'PIX', 10);

SELECT id, descricao, valor, status FROM cobrancas WHERE id = 13;

SELECT id, cobranca_id, valor, encargos, forma FROM pagamentos WHERE cobranca_id = 13;

SELECT cobranca_id, status_anterior, status_novo, usuario_banco FROM log_cobrancas;

DO $$
BEGIN
    INSERT INTO pagamentos (cobranca_id, valor, forma, pago_em)
    VALUES (20, 410.00, 'PIX', now());
    RAISE NOTICE 'ERRO: o pagamento da cobrança negociada passou.';
EXCEPTION WHEN raise_exception THEN
    RAISE NOTICE 'Gatilho barrou: %', SQLERRM;
END;
$$;

DO $$
DECLARE
    v_pagamento integer;
BEGIN
    CALL sp_registrar_pagamento(13, 'PIX', 10, 50.00, v_pagamento);
    RAISE NOTICE 'ERRO: a cobrança foi paga duas vezes.';
EXCEPTION WHEN raise_exception THEN
    RAISE NOTICE 'Gatilho barrou: %', SQLERRM;
END;
$$;

DO $$
BEGIN
    INSERT INTO pagamentos (cobranca_id, valor, forma, pago_em)
    VALUES (14, -5.00, 'PIX', now());
    RAISE NOTICE 'ERRO: o pagamento negativo passou.';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'Restrição CHECK barrou: %', SQLERRM;
END;
$$;

DO $$
BEGIN
    INSERT INTO cobrancas (unidade_id, competencia, descricao, valor, vencimento, status, origem)
    VALUES (999, date_trunc('month', CURRENT_DATE), 'Unidade que não existe', 100.00,
            CURRENT_DATE + 10, 'ABERTA', 'TAXA');
    RAISE NOTICE 'ERRO: a cobrança de unidade inexistente passou.';
EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'Chave estrangeira barrou: %', SQLERRM;
END;
$$;

DO $$
BEGIN
    INSERT INTO cobrancas (unidade_id, competencia, descricao, valor, vencimento, status, origem)
    VALUES (1, '2026-07-01', 'Taxa repetida', 320.00, '2026-07-10', 'ABERTA', 'TAXA');
    RAISE NOTICE 'ERRO: a taxa repetida passou.';
EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'Índice único barrou: %', SQLERRM;
END;
$$;

SET LOCAL enable_seqscan = off;

EXPLAIN
SELECT id, unidade_id, vencimento
  FROM cobrancas
 WHERE status IN ('ABERTA', 'VENCIDA')
   AND vencimento < CURRENT_DATE;

SET LOCAL ROLE smartcondo_portaria;

SELECT nome, apartamento, email FROM vw_moradores ORDER BY apartamento;

DO $$
DECLARE
    v_cpf text;
BEGIN
    SELECT cpf INTO v_cpf FROM usuarios LIMIT 1;
    RAISE NOTICE 'ERRO: a portaria leu o CPF.';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'Permissão barrou: %', SQLERRM;
END;
$$;

DO $$
BEGIN
    PERFORM 1 FROM pagamentos LIMIT 1;
    RAISE NOTICE 'ERRO: a portaria leu os pagamentos.';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'Permissão barrou: %', SQLERRM;
END;
$$;

RESET ROLE;

ROLLBACK;

SELECT id, descricao, status FROM cobrancas WHERE id = 13;
