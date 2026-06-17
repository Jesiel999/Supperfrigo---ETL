CREATE OR REPLACE VIEW vw_bi_pmp AS

SELECT
    pg.codigo_titulo                    AS codigo_titulo,
    pg.tenant_id                     AS tenant_id,

    pg.id_empresa                    AS id_empresa,
    e.nome_empresa                  AS nome_empresa,

    pg.id_pessoa                     AS id_pessoa,
    p.nome_pessoa                   AS nome_pessoa,

    pg.numero_documento              AS numero_documento,
    pg.ordem                         AS ordem,
    pg.origem                        AS origem,
    pg.descricao_forma_cobranca      AS descricao_forma_cobranca,

    pg.valor_total                   AS valor_total,

    pg.data_emissao                  AS data_emissao,
    pg.data_vencimento               AS data_vencimento,
    pg.data_baixa                    AS data_baixa,

    pg.dias_pagamento                AS dias_pagamento,

    pg.status_financeiro             AS status_financeiro,
    pg.descricao_situacao            AS descricao_situacao

FROM pmp_gold AS pg

LEFT JOIN empresa_bi e
    ON e.codigo_empresa = pg.id_empresa

LEFT JOIN pessoa_bi p
    ON p.codigo_pessoa = pg.id_pessoa

WHERE dias_pagamento IS NOT NULL