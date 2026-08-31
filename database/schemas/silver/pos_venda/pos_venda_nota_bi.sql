CREATE TABLE IF NOT EXISTS pos_venda_nota_bi (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codigo_posvenda BIGINT NOT NULL,
    codigo_origem BIGINT NOT NULL,

    tipo VARCHAR(20),
    descricao VARCHAR(255),

    codigo_nota BIGINT,
    numero_nota BIGINT,
    chave_nota VARCHAR(100),

    data_faturamento DATETIME,
    operacao VARCHAR(255),

    data_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_posvenda (
        codigo_posvenda
    ),

    KEY idx_nota (
        codigo_nota
    ),

    KEY idx_data (
        data_faturamento
    )

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;