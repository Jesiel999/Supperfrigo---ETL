CREATE TABLE IF NOT EXISTS pipeline_offset (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL,
    origem VARCHAR(50) NOT NULL,
    offset_atual INT NOT NULL DEFAULT 1,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uk_pipeline_offset_tenant_origem
        UNIQUE (tenant_id, origem),

    CONSTRAINT pipeline_ibfk_1
        FOREIGN KEY (tenant_id)
        REFERENCES tenant (id)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;