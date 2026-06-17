CREATE OR REPLACE VIEW vw_bi_pmr AS

SELECT
    r.codigo_titulo                    AS codigo_titulo,
    r.tenant_id                     AS tenant_id,

    r.id_empresa                    AS id_empresa,
    e.nome_empresa                  AS nome_empresa,

    r.id_pessoa                     AS id_pessoa,
    p.nome_pessoa                   AS nome_pessoa,

    r.numero_documento              AS numero_documento,
    r.ordem                         AS ordem,
    r.origem                        AS origem,
    r.descricao_forma_cobranca      AS descricao_forma_cobranca,

    r.valor_total                   AS valor_total,

    r.data_emissao                  AS data_emissao,
    r.data_vencimento               AS data_vencimento,
    r.data_baixa                    AS data_baixa,

    r.dias_recebimento                AS dias_recebimento,

    r.status_financeiro             AS status_financeiro,
    r.descricao_situacao            AS descricao_situacao

FROM pmr_gold AS r

LEFT JOIN empresa_bi e
    ON e.codigo_empresa = r.id_empresa

LEFT JOIN pessoa_bi p
    ON p.codigo_pessoa = r.id_pessoa

WHERE dias_recebimento IS NOT NULL