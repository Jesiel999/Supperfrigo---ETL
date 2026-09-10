CREATE OR REPLACE VIEW vw_bi_telemetria_frota AS

WITH ultima_telemetria AS (
    SELECT
        t.id,
        t.tenant_id,
        t.veiculo_id,
        t.dispositivo_id,
        t.data_evento,

        ROW_NUMBER() OVER (
            PARTITION BY t.tenant_id, t.veiculo_id
            ORDER BY t.data_evento DESC, t.id DESC
        ) AS rn

    FROM telemetria_bi t
    WHERE t.dados_validos = 1
)

SELECT
    tenant_id,

    COUNT(DISTINCT veiculo_id) AS total_veiculos,

    COUNT(
        DISTINCT CASE
            WHEN rn = 1
                 AND dispositivo_id IS NOT NULL
                 AND dispositivo_id <> '0'
            THEN veiculo_id
        END
    ) AS veiculos_em_operacao,

    COUNT(
        DISTINCT CASE
            WHEN rn = 1
                 AND (
                     dispositivo_id IS NULL
                     OR dispositivo_id = '0'
                 )
            THEN veiculo_id
        END
    ) AS veiculos_fora_operacao

FROM ultima_telemetria

GROUP BY tenant_id;