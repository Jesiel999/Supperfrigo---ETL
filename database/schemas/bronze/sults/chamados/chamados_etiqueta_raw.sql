CREATE TABLE IF NOT EXISTS chamados_etiqueta_raw (

    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id           INT NOT NULL,

    chamado_codigo      INT NOT NULL,

    etiqueta_id         INT,
    etiqueta_nome       VARCHAR(255),
    etiqueta_cor        VARCHAR(20),

    criado_em           DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_chamado (tenant_id, chamado_codigo)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;