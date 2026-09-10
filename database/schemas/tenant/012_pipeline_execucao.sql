CREATE TABLE IF NOT EXISTS pipeline_execucao (
    id BIGINT NOT NULL AUTO_INCREMENT,

    pipeline_offset_id INT NOT NULL,
    tenant_id INT NOT NULL,

    inicio_execucao DATETIME(3) NOT NULL,
    fim_execucao DATETIME(3) NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'EXECUTANDO',

    offset_inicial BIGINT NULL,
    offset_final BIGINT NULL,

    tempo_total_segundos DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    velocidade_reg_por_segundo DECIMAL(12,2) NOT NULL DEFAULT 0.00,

    total_processados BIGINT NOT NULL DEFAULT 0,
    total_inseridos BIGINT NOT NULL DEFAULT 0,
    total_atualizados BIGINT NOT NULL DEFAULT 0,
    total_ignorados BIGINT NOT NULL DEFAULT 0,
    total_erros BIGINT NOT NULL DEFAULT 0,

    mensagem_erro TEXT NULL,

    criado_em DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),

    PRIMARY KEY (id),

    KEY idx_pipeline_execucao_offset (
        pipeline_offset_id
    ),

    KEY idx_pipeline_execucao_tenant (
        tenant_id
    ),

    KEY idx_pipeline_execucao_inicio (
        tenant_id,
        inicio_execucao
    ),

    KEY idx_pipeline_execucao_status (
        status
    ),

    CONSTRAINT fk_pipeline_execucao_offset
        FOREIGN KEY (pipeline_offset_id)
        REFERENCES pipeline_offset (id),

    CONSTRAINT fk_pipeline_execucao_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant (id)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;