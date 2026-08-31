CREATE TABLE IF NOT EXISTS pos_venda_nota_raw (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codposv BIGINT UNSIGNED NOT NULL,

    tipo VARCHAR(20),
    descricao VARCHAR(255),

    codigo_nota BIGINT,
    numero_nota BIGINT,
    chave_nota VARCHAR(100),

    data_faturamento DATETIME,
    operacao VARCHAR(255),

    KEY idx_posv (
        codposv
    ),

    KEY idx_nota (
        codigo_nota
    ),

    KEY idx_numero (
        numero_nota
    ),

    CONSTRAINT fk_posv
        FOREIGN KEY (codposv)
        REFERENCES pos_venda_raw (codigo)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;