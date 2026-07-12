CREATE OR REPLACE VIEW vw_bi_inadimplencia AS

SELECT
    f.id_empresa               AS id_empresa,
    e.nome_empresa             AS nome_empresa,
    f.id_pessoa                AS id_pessoa,
    p.nome_pessoa              AS nome_pessoa,
    f.numero_documento         AS numero_documento,
    f.ordem                    AS ordem,
    f.origem                   AS origem,
    f.descricao_forma_cobranca AS descricao_forma_cobranca,
    f.valor_total              AS valor_total,
    f.data_vencimento          AS data_vencimento,
    f.data_baixa               AS data_baixa,
    f.dias_atraso              AS dias_atraso,
    f.status_financeiro        AS status_financeiro,
    f.descricao_situacao       AS descricao_situacao,

    (
        SELECT MAX(fb.atualizado_em)
        FROM inadimplencia_gold fb
    ) AS ultima_atualizacao

FROM inadimplencia_gold f

LEFT JOIN empresa_bi e
    ON e.codigo_empresa = f.id_empresa

LEFT JOIN pessoa_bi p
    ON p.codigo_pessoa = f.id_pessoa

WHERE
    f.descricao_situacao IS NULL
    OR UPPER(f.descricao_situacao) NOT IN (
        'CANCELADO',
        'UNIDO',
        'RENEGOCIADO',
        'BAIXADO',
        'BAIXADO PARCIAL'
    );