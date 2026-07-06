CREATE TABLE IF NOT EXISTS chamados_apoio_raw (

    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id               INT NOT NULL,

    chamado_codigo          INT NOT NULL,

    pessoa_id               INT,
    pessoa_nome             VARCHAR(255),

    departamento_id         INT,
    departamento_nome       VARCHAR(100),

    pessoa_unidade          BOOLEAN,

    criado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_chamado (tenant_id, chamado_codigo)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;