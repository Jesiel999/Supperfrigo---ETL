CREATE OR REPLACE
VIEW `vw_bi_taxa_pagamento` AS
SELECT
    f.codigo_raw AS codigo,
    f.id_empresa AS id_empresa,
    e.nome_empresa AS nome_empresa,
    f.id_pessoa AS id_pessoa,
    p.nome_pessoa AS nome_pessoa,
    f.numero_documento AS numero_documento,
    f.ordem AS ordem,
    f.origem AS origem,
    f.descricao_forma_cobranca AS descricao_forma_cobranca,
    f.valor_total AS valor_total,
    f.data_vencimento AS data_vencimento,
    f.data_baixa AS data_baixa,
    f.status_financeiro AS status_financeiro,
    f.descricao_situacao AS descricao_situacao,
    (
        SELECT MAX(fb.atualizado_em)
        FROM financeiro_bi fb
    ) AS ultima_atualização
FROM financeiro_bi f
LEFT JOIN empresa_bi e
    ON e.codigo_empresa = f.id_empresa
LEFT JOIN pessoa_bi p
    ON p.codigo_pessoa = f.id_pessoa
WHERE
    f.tipo_titulo = 'PAGAR'
    AND UPPER(f.descricao_situacao) IN ('EM ABERTO', 'TRÂNSITO', 'BAIXADO', 'BAIXADO PARCIAL')