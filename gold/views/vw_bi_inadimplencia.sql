CREATE OR REPLACE VIEW vw_bi_inadimplencia AS

SELECT
    f.codigo_raw AS codigo,
    f.id_empresa AS id_empresa,
    e.nome_empresa AS nome_empresa,
    f.id_pessoa AS id_pessoa,
    p.nome AS nome_pessoa,
    f.numero_documento AS numero_documento,
    f.ordem AS ordem,
    f.origem AS origem,
    f.descricao_forma_cobranca AS descricao_forma_cobranca,
    f.valor_total AS valor_total,
    f.data_vencimento AS data_vencimento,
    f.data_baixa AS data_baixa,
    f.dias_atraso AS dias_atraso,
    f.status_financeiro AS status_financeiro,
    f.descricao_situacao AS descricao_situacao,

    (
        SELECT MAX(fb.atualizado_em)
        FROM financeiro_bi fb
    ) AS ultima_atualizacao

FROM financeiro_bi f

LEFT JOIN (
    SELECT
        codigo_empresa,
        MAX(nome_empresa) AS nome_empresa
    FROM empresa_bi
    GROUP BY codigo_empresa
) e
    ON e.codigo_empresa = f.id_empresa

LEFT JOIN (
    SELECT
        id_sances,
        MAX(nome) AS nome
    FROM pessoa_bi
    GROUP BY id_sances
) p
    ON p.id_sances = f.id_pessoa

WHERE
    f.tipo_titulo = 'RECEBER'
    AND f.status_financeiro = 'VENCIDO'
    AND UPPER(f.descricao_situacao) IN (
        'EM ABERTO',
        'TRÂNSITO'
    );