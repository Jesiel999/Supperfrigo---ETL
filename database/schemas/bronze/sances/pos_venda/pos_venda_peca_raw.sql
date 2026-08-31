CREATE TABLE IF NOT EXISTS pos_venda_peca_raw (
   id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codposv BIGINT UNSIGNED NOT NULL,

    codigo_peca BIGINT,
    referencia_peca VARCHAR(100),
    descricao_peca VARCHAR(255),
    unidade_peca VARCHAR(30),

    qtd_peca DECIMAL(15,4),
    valor_unitario DECIMAL(15,4),
    custo_unitario DECIMAL(15,4),
    custo_total DECIMAL(15,2),

    total_bruto DECIMAL(15,2),
    valor_desconto DECIMAL(15,2),
    total_liquido DECIMAL(15,2),

    codigo_mecanico BIGINT,
    nome_mecanico VARCHAR(255),

    percentual_comissao_mecanico DECIMAL(10,4),
    valor_comissao_mecanico DECIMAL(15,2),

    peca_cancelada BOOLEAN NOT NULL DEFAULT FALSE,

    codigo_motivo_cancelamento BIGINT,
    descricao_motivo_cancelamento VARCHAR(255),

    KEY idx_posv (
        codposv
    ),

    KEY idx_peca (
        codigo_peca
    ),

    CONSTRAINT fk_posv
        FOREIGN KEY (codposv)
        REFERENCES pos_venda_raw (codigo)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;