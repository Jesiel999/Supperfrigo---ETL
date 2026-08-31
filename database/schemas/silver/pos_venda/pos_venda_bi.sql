CREATE TABLE IF NOT EXISTS pos_venda_bi (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INTEGER NOT NULL,  

    codigo BIGINT UNSIGNED NOT NULL,
    codigo_origem BIGINT NOT NULL,

    tipo INT NOT NULL,
    descricao_tipo VARCHAR(100),

    orcamento_os BOOLEAN NOT NULL DEFAULT FALSE,
    numero BIGINT,

    codigo_situacao VARCHAR(10),
    situacao VARCHAR(100),

    aguardando_liberacao BOOLEAN NOT NULL DEFAULT FALSE,

    codigo_empresa BIGINT,
    nome_empresa VARCHAR(255),

    codigo_cliente BIGINT,
    nome_cliente VARCHAR(255),

    codigo_tipo_preco BIGINT,
    descricao_tipo_preco VARCHAR(255),

    codigo_veiculo BIGINT,
    placa_veiculo VARCHAR(20),

    codigo_modelo_veiculo BIGINT,
    descricao_modelo_veiculo VARCHAR(255),

    codigo_cor_veiculo BIGINT,
    descricao_cor_veiculo VARCHAR(255),

    ano_fabricacao_veiculo SMALLINT,
    ano_modelo_veiculo SMALLINT,

    codigo_tipo_os BIGINT,
    descricao_tipo_os VARCHAR(255),

    km_entrada DECIMAL(15,2),
    km_saida DECIMAL(15,2),

    data_entrada DATETIME,
    data_saida DATETIME,

    solicitacao_cliente TEXT,
    avaria TEXT,
    defeito_averiguado TEXT,

    codigo_proprietario BIGINT,
    nome_proprietario VARCHAR(255),

    codigo_tipo_midia BIGINT,
    descricao_tipo_midia VARCHAR(255),

    codigo_modalidade_venda BIGINT,
    descricao_modalidade_venda VARCHAR(255),

    codigo_conveniado BIGINT,
    nome_conveniado VARCHAR(255),

    codigo_consultor BIGINT,
    nome_consultor VARCHAR(255),

    percentual_comissao_peca DECIMAL(10,4),
    valor_comissao_peca_consultor DECIMAL(15,2),

    percentual_comissao_servico DECIMAL(10,4),
    valor_comissao_servico_consultor DECIMAL(15,2),

    total_comissao_consultor DECIMAL(15,2),

    codigo_usuario_insercao BIGINT,
    nome_usuario_insercao VARCHAR(255),
    data_insercao DATETIME,

    codigo_usuario_alteracao BIGINT,
    nome_usuario_alteracao VARCHAR(255),
    data_alteracao DATETIME,

    codigo_usuario_cancelamento BIGINT,
    nome_usuario_cancelamento VARCHAR(255),
    data_cancelamento DATETIME,

    codigo_usuario_fechamento BIGINT,
    nome_usuario_fechamento VARCHAR(255),
    data_fechamento DATETIME,

    valor_seguro DECIMAL(15,2),
    valor_frete DECIMAL(15,2),
    valor_despesas DECIMAL(15,2),
    valor_acrescimo_financeiro DECIMAL(15,2),

    total_pecas_bruto DECIMAL(15,2),
    total_desconto_pecas DECIMAL(15,2),
    total_pecas_liquido DECIMAL(15,2),
    total_pecas_custo DECIMAL(15,2),
    total_pecas_lucro DECIMAL(15,2),

    total_servicos_bruto DECIMAL(15,2),
    total_desconto_servicos DECIMAL(15,2),
    total_servicos_liquido DECIMAL(15,2),
    total_servicos_custo DECIMAL(15,2),
    total_servicos_lucro DECIMAL(15,2),

    total_geral DECIMAL(15,2),

    codigo_condicao_pagamento BIGINT,
    descricao_condicao_pagamento VARCHAR(255),

    margem_pecas DECIMAL(10,4),
    margem_servicos DECIMAL(10,4),
    margem_total DECIMAL(10,4),

    ano INT,
    mes INT,
    mes_ano VARCHAR(7),

    data_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_codigo_origem (
        codigo_origem
    ),

    KEY idx_codigo (
        codigo
    ),

    KEY idx_empresa (
        codigo_empresa
    ),

    KEY idx_cliente (
        codigo_cliente
    ),

    KEY idx_consultor (
        codigo_consultor
    ),

    KEY idx_data_alteracao (
        data_alteracao
    ),

    KEY idx_data_insercao (
        data_insercao
    ),

    KEY idx_situacao (
        codigo_situacao
    ),

    KEY idx_ano_mes (
        ano,
        mes
    )

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;