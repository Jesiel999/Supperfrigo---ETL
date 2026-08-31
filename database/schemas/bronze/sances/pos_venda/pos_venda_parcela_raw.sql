CREATE TABLE IF NOT EXISTS pos_venda_parcela_raw (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codposv BIGINT UNSIGNED NOT NULL,

    tipo_parcela ENUM(
        'PECA',
        'SERVICO',
        'FRANQUIA'
    ) NOT NULL,

    ordem_parcela VARCHAR(20),
    vencimento_parcela DATE,
    forma_cobranca_parcela VARCHAR(255),
    valor_parcela DECIMAL(15,2),

    KEY idx_posv (
        codposv
    ),

    KEY idx_tipo (
        tipo_parcela
    ),

    KEY idx_vencimento (
        vencimento_parcela
    ),

    CONSTRAINT fk_posv
        FOREIGN KEY (codposv)
        REFERENCES pos_venda_raw (codigo)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;