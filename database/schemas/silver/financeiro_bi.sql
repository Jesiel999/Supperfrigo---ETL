CREATE TABLE IF NOT EXISTS financeiro_bi (

    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,

    codigo_raw                  VARCHAR(50) NOT NULL UNIQUE,

    -- Empresa
    id_empresa                  VARCHAR(50),

    -- Pessoa / Cliente-Fornecedor
    id_pessoa                   VARCHAR(50),

    -- Documento
    tipo_titulo                 VARCHAR(20),
    numero_documento            VARCHAR(100),
    ordem                       VARCHAR(50),
    origem                      VARCHAR(100),

    -- Situação
    codigo_situacao             VARCHAR(50),
    descricao_situacao          VARCHAR(255),
    status_financeiro           VARCHAR(50),  -- PAGO | EM_ABERTO | VENCIDO | CANCELADO

    -- Forma cobrança / pagamento
    descricao_forma_cobranca    VARCHAR(255),
    descricao_forma_pagamento   VARCHAR(255),

    -- Categoria / Centro de Custo / Conta Resultado
    codigo_categoria_financeira VARCHAR(50),
    descricao_categoria_financeira VARCHAR(255),
    codigo_centro_custo         VARCHAR(50),
    descricao_centro_custo      VARCHAR(255),
    codigo_conta_resultado      VARCHAR(50),
    descricao_conta_resultado   VARCHAR(255),

    -- Datas
    data_emissao                DATE,
    data_competencia            DATE,
    data_vencimento             DATE,
    data_baixa                  DATE,
    data_cancelamento           DATE,

    -- Valores
    valor_nominal               DECIMAL(15, 2),
    valor_multa                 DECIMAL(15, 2),
    acrescimo                   DECIMAL(15, 2),
    valor_total                 DECIMAL(15, 2),

    -- Indicadores calculados
    dias_atraso                 INT,           -- dias entre hoje e data_vencimento (se em aberto)
    dias_pagamento              INT,
    dias_recebimento            INT,

    -- Controle
    criado_em                   DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_id_empresa        (id_empresa),
    INDEX idx_id_pessoa         (id_pessoa),
    INDEX idx_tipo_titulo       (tipo_titulo),
    INDEX idx_status_financeiro (status_financeiro),
    INDEX idx_data_vencimento   (data_vencimento),
    INDEX idx_data_baixa        (data_baixa)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
