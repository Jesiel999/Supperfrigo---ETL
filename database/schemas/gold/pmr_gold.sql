CREATE TABLE IF NOT EXISTS pmr_gold (

    codigo                          BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo_titulo                   INTEGER NOT NULL,

    tenant_id                       INTEGER NOT NULL,
    
    -- Empresa
    id_empresa                  VARCHAR(50),

    -- Pessoa / Cliente-Fornecedor
    id_pessoa                   VARCHAR(50),

    -- Documento
    numero_documento            VARCHAR(50),
    ordem                       VARCHAR(50),
    origem                      VARCHAR(100),

    -- Forma cobrança / pagamento
    descricao_forma_cobranca    VARCHAR(255),

    -- Valor
    valor_total                 DECIMAL(15, 2),

    
    -- Datas
    data_emissao                DATE,
    data_vencimento             DATE,
    data_baixa                  DATE,
    dias_recebimento            INT,

    -- Forma cobrança / pagamento
    status_financeiro           VARCHAR(50),
    descricao_situacao          VARCHAR(255),
    
    -- Controle
    processado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_id_empresa    (id_empresa),
    INDEX idx_id_pessoa     (id_pessoa),
    INDEX idx_status        (status_financeiro)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
