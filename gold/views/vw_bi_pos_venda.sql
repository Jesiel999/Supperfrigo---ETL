CREATE OR REPLACE VIEW vw_bi_pos_venda AS
SELECT
    p.codigo,
    p.codigo_origem,

    p.tipo,
    p.descricao_tipo,

    p.numero,

    p.codigo_empresa,
    p.nome_empresa,

    p.codigo_cliente,
    p.nome_cliente,

    p.codigo_consultor,
    p.nome_consultor,

    p.codigo_situacao,
    p.situacao,

    p.codigo_tipo_os,
    p.descricao_tipo_os,

    p.placa_veiculo,
    p.descricao_modelo_veiculo,

    p.data_entrada,
    p.data_saida,

    p.data_insercao,
    p.data_alteracao,
    p.data_fechamento,

    p.valor_seguro,
    p.valor_frete,
    p.valor_despesas,
    p.valor_acrescimo_financeiro,

    COALESCE(p.total_pecas_bruto, 0)
        AS total_pecas_bruto,

    COALESCE(p.total_desconto_pecas, 0)
        AS total_desconto_pecas,

    COALESCE(p.total_pecas_liquido, 0)
        AS total_pecas_liquido,

    COALESCE(p.total_pecas_custo, 0)
        AS total_pecas_custo,

    COALESCE(p.total_pecas_lucro, 0)
        AS total_pecas_lucro,

    COALESCE(p.total_servicos_bruto, 0)
        AS total_servicos_bruto,

    COALESCE(p.total_desconto_servicos, 0)
        AS total_desconto_servicos,

    COALESCE(p.total_servicos_liquido, 0)
        AS total_servicos_liquido,

    COALESCE(p.total_servicos_custo, 0)
        AS total_servicos_custo,

    COALESCE(p.total_servicos_lucro, 0)
        AS total_servicos_lucro,

    COALESCE(p.total_geral, 0)
        AS total_geral,

    p.total_comissao_consultor,

    CASE
        WHEN COALESCE(p.total_pecas_liquido, 0) > 0
        THEN
            (
                p.total_pecas_lucro /
                p.total_pecas_liquido
            ) * 100
        ELSE 0
    END AS margem_pecas,

    CASE
        WHEN COALESCE(p.total_servicos_liquido, 0) > 0
        THEN
            (
                p.total_servicos_lucro /
                p.total_servicos_liquido
            ) * 100
        ELSE 0
    END AS margem_servicos,

    CASE
        WHEN COALESCE(p.total_geral, 0) > 0
        THEN
            (
                (
                    COALESCE(p.total_pecas_lucro, 0)
                    +
                    COALESCE(p.total_servicos_lucro, 0)
                )
                /
                p.total_geral
            ) * 100
        ELSE 0
    END AS margem_total,

    YEAR(p.data_insercao) AS ano,

    MONTH(p.data_insercao) AS mes,

    DATE_FORMAT(
        p.data_insercao,
        '%Y-%m'
    ) AS mes_ano

FROM bi_pos_venda p;