CREATE TABLE IF NOT EXISTS financeiro_raw (

    id                              BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id                       INTEGER NOT NULL,

    codigo                          VARCHAR(50)  NOT NULL UNIQUE,
    tipo_titulo                     VARCHAR(20),

    codigo_empresa                  VARCHAR(50),
    nome_empresa                    VARCHAR(255),

    codigo_situacao                 VARCHAR(50),
    descricao_situacao              VARCHAR(255),

    codigo_pessoa                   VARCHAR(50),
    nome_pessoa                     VARCHAR(255),

    codigo_cliente_fornecedor       VARCHAR(50),
    nome_cliente_fornecedor         VARCHAR(255),

    titulo_previsao                 VARCHAR(10),
    criado_manualmente              VARCHAR(10),

    origem                          VARCHAR(100),
    codigo_origem                   VARCHAR(50),

    numero_documento                VARCHAR(100),
    ordem                           VARCHAR(50),

    codigo_forma_cobranca           VARCHAR(50),
    descricao_forma_cobranca        VARCHAR(255),

    codigo_vendedor                 VARCHAR(50),
    descricao_vendedor              VARCHAR(255),

    historico                       TEXT,

    codigo_grupo                    VARCHAR(50),
    descricao_grupo                 VARCHAR(255),

    codigo_departamento             VARCHAR(50),
    descricao_departamento          VARCHAR(255),

    observacao                      TEXT,
    observacoes_boleto              TEXT,

    codigo_barras                   VARCHAR(100),

    codigo_forma_pagamento          VARCHAR(50),
    descricao_forma_pagamento       VARCHAR(255),

    codigo_categoria_financeira     VARCHAR(50),
    descricao_categoria_financeira  VARCHAR(255),

    codigo_convenio                 VARCHAR(50),
    descricao_convenio              VARCHAR(255),

    codigo_conveniado               VARCHAR(50),
    descricao_conveniado            VARCHAR(255),

    codigo_aprovador                VARCHAR(50),
    nome_aprovador                  VARCHAR(255),

    nosso_numero                    VARCHAR(100),
    numero_remessa                  VARCHAR(100),

    titulo_origem                   VARCHAR(100),
    titulo_gerado                   VARCHAR(100),

    codigo_conta_patrimonial        VARCHAR(50),
    numero_conta_patrimonial        VARCHAR(100),
    descricao_conta_patrimonial     VARCHAR(255),

    codigo_conta_resultado          VARCHAR(50),
    numero_conta_resultado          VARCHAR(100),
    descricao_conta_resultado       VARCHAR(255),

    codigo_centro_custo             VARCHAR(50),
    descricao_centro_custo          VARCHAR(255),

    data_emissao                    DATETIME,
    data_competencia                DATETIME,
    data_vencimento                 DATETIME,

    codigo_usuario_insercao         VARCHAR(50),
    nome_usuario_insercao           VARCHAR(255),
    data_insercao                   DATETIME,

    codigo_usuario_alteracao        VARCHAR(50),
    nome_usuario_alteracao          VARCHAR(255),
    data_alteracao                  DATETIME,

    codigo_usuario_cancelamento     VARCHAR(50),
    nome_usuario_cancelamento       VARCHAR(255),
    data_cancelamento               DATETIME,

    motivo_cancelamento             TEXT,

    codigo_usuario_baixa            VARCHAR(50),
    nome_usuario_baixa              VARCHAR(255),
    data_baixa                      DATETIME,

    codigo_usuario_aprovacao        VARCHAR(50),
    nome_usuario_aprovacao          VARCHAR(255),
    data_aprovacao                  DATETIME,

    valor_nominal                   DECIMAL(15, 2),
    valor_multa                     DECIMAL(15, 2),

    percentual_multa                DECIMAL(10, 4),
    percentual_juros                DECIMAL(10, 4),

    taxa_boleto                     DECIMAL(15, 2),
    juros_crediario_proprio         DECIMAL(15, 2),

    acrescimo                       DECIMAL(15, 2),
    valor_total                     DECIMAL(15, 2),

    criado_em                       DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em                   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_codigo_empresa    (codigo_empresa),
    INDEX idx_codigo_pessoa     (codigo_pessoa),
    INDEX idx_tipo_titulo       (tipo_titulo),
    INDEX idx_codigo_situacao   (codigo_situacao),
    INDEX idx_data_vencimento   (data_vencimento),
    INDEX idx_data_baixa        (data_baixa),
    INDEX idx_data_alteracao    (data_alteracao)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
