SELECT u.numero AS apartamento,
       u.andar,
       m.nome AS morador,
       m.tipo_ocupacao,
       CASE WHEN m.reside THEN 'sim' ELSE 'não' END AS mora_no_apartamento
  FROM usuarios m
  JOIN unidades u ON u.id = m.unidade_id
 WHERE m.papel = 'MORADOR'
   AND m.status = 'ATIVO'
 ORDER BY u.numero, m.nome;

SELECT u.numero AS apartamento,
       u.andar,
       u.vagas_garagem
  FROM unidades u
 WHERE NOT EXISTS (
         SELECT 1
           FROM usuarios m
          WHERE m.unidade_id = u.id
            AND m.papel = 'MORADOR'
            AND m.status = 'ATIVO'
            AND m.reside
       )
 ORDER BY u.numero;

SELECT u.numero AS apartamento,
       COUNT(c.id) AS cobrancas,
       COALESCE(SUM(c.valor), 0) AS total_cobrado,
       COALESCE(SUM(p.pago), 0) AS total_pago,
       COALESCE(SUM(c.valor - COALESCE(p.pago, 0))
                FILTER (WHERE c.status IN ('ABERTA', 'VENCIDA')), 0) AS em_aberto
  FROM unidades u
  LEFT JOIN cobrancas c
         ON c.unidade_id = u.id
        AND c.status NOT IN ('CANCELADA', 'NEGOCIADA')
  LEFT JOIN (SELECT cobranca_id, SUM(valor - encargos) AS pago
               FROM pagamentos
              GROUP BY cobranca_id) p
         ON p.cobranca_id = c.id
 GROUP BY u.id, u.numero
 ORDER BY u.numero;

SELECT u.numero AS apartamento,
       COUNT(*) AS cobrancas_em_atraso,
       SUM(c.valor - COALESCE(p.pago, 0)) AS valor_devido,
       MAX(CURRENT_DATE - c.vencimento) AS dias_de_atraso
  FROM cobrancas c
  JOIN unidades u ON u.id = c.unidade_id
  LEFT JOIN (SELECT cobranca_id, SUM(valor - encargos) AS pago
               FROM pagamentos
              GROUP BY cobranca_id) p
         ON p.cobranca_id = c.id
 WHERE c.status IN ('ABERTA', 'VENCIDA')
   AND c.vencimento < CURRENT_DATE
 GROUP BY u.numero
HAVING SUM(c.valor - COALESCE(p.pago, 0)) > 0
 ORDER BY valor_devido DESC, u.numero;

SELECT to_char(c.competencia, 'MM/YYYY') AS competencia,
       SUM(c.valor) AS cobrado,
       COALESCE(SUM(p.pago), 0) AS recebido,
       ROUND(100 * (1 - COALESCE(SUM(p.pago), 0) / SUM(c.valor)), 1) AS inadimplencia_pct
  FROM cobrancas c
  LEFT JOIN (SELECT cobranca_id, SUM(valor - encargos) AS pago
               FROM pagamentos
              GROUP BY cobranca_id) p
         ON p.cobranca_id = c.id
 WHERE c.origem = 'TAXA'
   AND c.status NOT IN ('CANCELADA', 'NEGOCIADA')
 GROUP BY c.competencia
 ORDER BY c.competencia;

SELECT categoria,
       COUNT(*) AS lancamentos,
       SUM(valor) AS total,
       ROUND(100 * SUM(valor) / SUM(SUM(valor)) OVER (), 1) AS participacao_pct
  FROM despesas
 WHERE inativo_em IS NULL
 GROUP BY categoria
 ORDER BY total DESC;

WITH receitas AS (
       SELECT date_trunc('month', pago_em AT TIME ZONE 'America/Campo_Grande')::date AS mes,
              SUM(valor) AS valor
         FROM pagamentos
        GROUP BY 1
     ),
     gastos AS (
       SELECT date_trunc('month', data)::date AS mes,
              SUM(valor) AS valor
         FROM despesas
        WHERE inativo_em IS NULL
        GROUP BY 1
     )
SELECT to_char(COALESCE(r.mes, g.mes), 'MM/YYYY') AS mes,
       COALESCE(r.valor, 0) AS receitas,
       COALESCE(g.valor, 0) AS despesas,
       COALESCE(r.valor, 0) - COALESCE(g.valor, 0) AS saldo_do_mes,
       SUM(COALESCE(r.valor, 0) - COALESCE(g.valor, 0))
           OVER (ORDER BY COALESCE(r.mes, g.mes)) AS saldo_acumulado
  FROM receitas r
  FULL JOIN gastos g ON g.mes = r.mes
 ORDER BY COALESCE(r.mes, g.mes);

SELECT e.nome AS espaco,
       e.capacidade,
       e.taxa_uso,
       COUNT(r.id) AS reservas,
       COUNT(r.id) FILTER (WHERE r.status = 'APROVADA') AS aprovadas,
       COUNT(r.id) FILTER (WHERE r.status = 'PENDENTE') AS pendentes,
       COUNT(r.id) FILTER (WHERE r.status = 'CONCLUIDA') AS concluidas,
       ROUND(COALESCE(SUM(EXTRACT(EPOCH FROM r.hora_fim - r.hora_inicio) / 3600)
                      FILTER (WHERE r.status IN ('APROVADA', 'CONCLUIDA')), 0), 1) AS horas_ocupadas
  FROM espacos_comuns e
  LEFT JOIN reservas r ON r.espaco_id = e.id
 WHERE e.reservavel
   AND e.inativo_em IS NULL
 GROUP BY e.id, e.nome, e.capacidade, e.taxa_uso
 ORDER BY reservas DESC, e.nome;

SELECT i.ordem,
       i.titulo,
       i.maioria,
       COUNT(v.id) FILTER (WHERE v.escolha = 'A_FAVOR') AS a_favor,
       COUNT(v.id) FILTER (WHERE v.escolha = 'CONTRA') AS contra,
       COUNT(v.id) FILTER (WHERE v.escolha = 'ABSTENCAO') AS abstencao,
       t.unidades,
       CASE i.maioria
         WHEN 'SIMPLES' THEN
           COUNT(v.id) FILTER (WHERE v.escolha = 'A_FAVOR')
             > COUNT(v.id) FILTER (WHERE v.escolha = 'CONTRA')
         WHEN 'DOIS_TERCOS' THEN
           3 * COUNT(v.id) FILTER (WHERE v.escolha = 'A_FAVOR') >= 2 * t.unidades
         ELSE
           COUNT(v.id) FILTER (WHERE v.escolha = 'A_FAVOR') = t.unidades
       END AS aprovado
  FROM assembleias a
  JOIN itens_pauta i ON i.assembleia_id = a.id
  LEFT JOIN votos v ON v.item_id = i.id
 CROSS JOIN LATERAL (
         SELECT COUNT(*) AS unidades
           FROM unidades u
          WHERE u.condominio_id = a.condominio_id
            AND NOT u.pendente
       ) t
 WHERE a.id = 1
 GROUP BY i.id, i.ordem, i.titulo, i.maioria, t.unidades
 ORDER BY i.ordem;

SELECT u.numero AS apartamento,
       CASE WHEN u.id IN (SELECT v.unidade_id
                            FROM votos v
                            JOIN itens_pauta i ON i.id = v.item_id
                           WHERE i.assembleia_id = 1)
            THEN 'votou'
            ELSE 'não votou'
       END AS participacao
  FROM unidades u
 WHERE u.condominio_id = 1
 ORDER BY u.numero;

SELECT numero AS apartamento,
       fracao_ideal,
       ROUND(42000 * fracao_ideal / SUM(fracao_ideal) OVER (), 2) AS parte_na_obra,
       ROUND(42000 * fracao_ideal / SUM(fracao_ideal) OVER () / 6, 2) AS parcela_mensal
  FROM unidades
 WHERE condominio_id = 1
 ORDER BY numero;

SELECT tipo, apartamento, descricao,
       to_char(desde AT TIME ZONE 'America/Campo_Grande', 'DD/MM/YYYY HH24:MI') AS desde,
       CURRENT_DATE - (desde AT TIME ZONE 'America/Campo_Grande')::date AS dias
  FROM (
         SELECT 'Encomenda para retirar' AS tipo, u.numero AS apartamento,
                e.remetente AS descricao, e.recebida_em AS desde
           FROM encomendas e
           JOIN unidades u ON u.id = e.unidade_id
          WHERE e.status = 'AGUARDANDO_RETIRADA'
         UNION ALL
         SELECT 'Visitante dentro', u.numero, v.nome, v.entrada_em
           FROM visitantes v
           JOIN unidades u ON u.id = v.unidade_id
          WHERE v.status = 'DENTRO'
       ) pendencias
 ORDER BY pendencias.desde;

SELECT nome,
       periodicidade_meses,
       proximo_vencimento,
       proximo_vencimento - CURRENT_DATE AS dias_restantes,
       CASE
         WHEN proximo_vencimento < CURRENT_DATE THEN 'VENCIDA'
         WHEN proximo_vencimento - CURRENT_DATE <= antecedencia_aviso_dias THEN 'AVISAR'
         ELSE 'EM DIA'
       END AS situacao
  FROM planos_manutencao
 WHERE inativo_em IS NULL
 ORDER BY proximo_vencimento;

SELECT to_char(r.feito_em AT TIME ZONE 'America/Campo_Grande', 'DD/MM/YYYY HH24:MI') AS quando,
       us.nome AS quem,
       r.acao,
       r.entidade,
       r.entidade_id,
       r.descricao
  FROM registros_alteracao r
  JOIN usuarios us ON us.id = r.autor_id
 ORDER BY r.feito_em DESC, r.id DESC
 LIMIT 10;
