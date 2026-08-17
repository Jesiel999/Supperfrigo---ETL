CREATE TABLE IF NOT EXISTS estoque_empresa_raw (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id INT NOT NULL,

    codigo_produto INT NOT NULL,
    codigo_empresa INT NOT NULL,

    cnpj VARCHAR(20) NULL,
    nome_razao VARCHAR(255) NULL,
    nome_fantasia VARCHAR(255) NULL,
    apelido VARCHAR(255) NULL,

    qtd_estoque DECIMAL(18,4) NOT NULL DEFAULT 0,
    qtd_aplicadas DECIMAL(18,4) NOT NULL DEFAULT 0,
    qtd_reservada DECIMAL(18,4) NOT NULL DEFAULT 0,
    qtd_transito DECIMAL(18,4) NOT NULL DEFAULT 0,
    qtd_pedido DECIMAL(18,4) NOT NULL DEFAULT 0,
    qtd_bo DECIMAL(18,4) NOT NULL DEFAULT 0,

    data_extracao DATETIME NOT NULL,
    processado_em DATETIME NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_estoque_empresa_raw (
        tenant_id,
        codigo_produto,
        codigo_empresa,
    ),

    INDEX idx_estoque_empresa_produto (
        tenant_id,
        codigo_produto
    ),

    INDEX idx_estoque_empresa_empresa (
        tenant_id,
        codigo_empresa
    )
);