CREATE TABLE IF NOT EXISTS pos_venda_parcela_bi (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codigo_posvenda BIGINT NOT NULL,
    codigo_origem BIGINT NOT NULL,

    tipo_parcela ENUM(
        'PECA',
        'SERVICO',
        'FRANQUIA'
    ) NOT NULL,

    ordem_parcela VARCHAR(20),

    vencimento_parcela DATE,

    forma_cobranca_parcela VARCHAR(255),

    valor_parcela DECIMAL(15,2),

    data_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_posvenda (
        codigo_posvenda
    ),

    KEY idx_vencimento (
        vencimento_parcela
    ),

    KEY idx_tipo (
        tipo_parcela
    )

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;