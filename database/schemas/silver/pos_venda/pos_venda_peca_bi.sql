CREATE TABLE IF NOT EXISTS pos_venda_peca_bi (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codigo_posvenda BIGINT NOT NULL,
    codigo_origem BIGINT NOT NULL,

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

    peca_cancelada BOOLEAN,

    codigo_motivo_cancelamento BIGINT,
    descricao_motivo_cancelamento VARCHAR(255),

    data_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    KEY idx_posvenda (
        codigo_posvenda
    ),

    KEY idx_peca (
        codigo_peca
    ),

    KEY idx_origem (
        codigo_origem
    )

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;