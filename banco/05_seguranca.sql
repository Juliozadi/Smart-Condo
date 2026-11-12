DO $$
DECLARE
    v_papel text;
BEGIN
    FOREACH v_papel IN ARRAY ARRAY['smartcondo_sindico', 'smartcondo_portaria', 'smartcondo_conselho'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_papel) THEN
            EXECUTE format('DROP OWNED BY %I', v_papel);
        ELSE
            EXECUTE format('CREATE ROLE %I NOLOGIN', v_papel);
        END IF;
    END LOOP;
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION fn_total_pago, fn_encargos, fn_rateio FROM PUBLIC;
REVOKE EXECUTE ON PROCEDURE sp_gerar_taxa_mensal, sp_registrar_pagamento FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO smartcondo_sindico, smartcondo_portaria, smartcondo_conselho;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO smartcondo_sindico;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO smartcondo_sindico;
REVOKE INSERT, UPDATE ON registros_alteracao, log_cobrancas FROM smartcondo_sindico;
GRANT EXECUTE ON FUNCTION fn_total_pago, fn_encargos, fn_rateio TO smartcondo_sindico;
GRANT EXECUTE ON PROCEDURE sp_gerar_taxa_mensal, sp_registrar_pagamento TO smartcondo_sindico;

GRANT SELECT ON unidades, espacos_comuns, reservas, veiculos_unidade, autorizacoes_visita
   TO smartcondo_portaria;
GRANT SELECT (id, nome, papel, status, unidade_id) ON usuarios TO smartcondo_portaria;
GRANT SELECT ON vw_moradores TO smartcondo_portaria;
GRANT SELECT, INSERT, UPDATE ON visitantes, encomendas, movimentacoes_veiculo
   TO smartcondo_portaria;
GRANT USAGE ON SEQUENCE visitantes_id_seq, encomendas_id_seq, movimentacoes_veiculo_id_seq
   TO smartcondo_portaria;

GRANT SELECT ON vw_situacao_unidades, vw_balancete_mensal TO smartcondo_conselho;

SELECT r.papel,
       t.objeto,
       has_table_privilege(r.papel, t.objeto, 'SELECT') AS consulta,
       has_table_privilege(r.papel, t.objeto, 'INSERT') AS insere,
       has_table_privilege(r.papel, t.objeto, 'UPDATE') AS altera,
       has_table_privilege(r.papel, t.objeto, 'DELETE') AS apaga
  FROM (VALUES ('smartcondo_sindico'), ('smartcondo_portaria'), ('smartcondo_conselho')) r (papel)
 CROSS JOIN (VALUES ('cobrancas'), ('pagamentos'), ('usuarios'), ('visitantes'),
                    ('log_cobrancas'), ('vw_moradores'), ('vw_balancete_mensal')) t (objeto)
 ORDER BY r.papel, t.objeto;
