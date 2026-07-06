CREATE TABLE IF NOT EXISTS inadimplencia_gold (

    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id                       INTEGER NOT NULL,

    id_empresa                  VARCHAR(50),
    nome_empresa                VARCHAR(255),

    id_pessoa                   VARCHAR(50),
    nome_pessoa                 VARCHAR(255),

    numero_documento            VARCHAR(100),
    ordem                       VARCHAR(50),
    origem                      VARCHAR(100),

    descricao_forma_cobranca    VARCHAR(255),

    valor_total                 DECIMAL(15, 2),
    data_vencimento             DATE,
    data_baixa                  DATE,
    dias_atraso                 INT,

    status_financeiro           VARCHAR(50),
    descricao_situacao          VARCHAR(255),

    processado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_id_empresa        (id_empresa),
    INDEX idx_id_pessoa         (id_pessoa),
    INDEX idx_dias_atraso       (dias_atraso),
    INDEX idx_status            (status_financeiro)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
