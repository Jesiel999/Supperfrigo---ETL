CREATE TABLE IF NOT EXISTS chamados_raw (
    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,

    tenant_id                   INT NOT NULL,

    codigo                      INT NOT NULL,

    titulo                      TEXT,

    solicitante_id              INT,
    solicitante_nome            VARCHAR(255),

    responsavel_id              INT,
    responsavel_nome            VARCHAR(255),

    unidade_id                  INT,
    unidade_nome                VARCHAR(255),

    departamento_id             INT,
    departamento_nome           VARCHAR(100),

    departamento_envio_id       INT,
    departamento_envio_nome     VARCHAR(100),

    assunto_id                  INT,
    assunto_nome                VARCHAR(255),

    tipo                        INT,

    -- Datas
    data_aberto                 VARCHAR(20),
    data_resolvido              VARCHAR(20),
    data_concluido              VARCHAR(20),
    data_resolver_planejado     VARCHAR(20),
    data_resolver_estipulado    VARCHAR(20),

    avaliacao_nota              INT,
    avaliacao_observacao        TEXT,

    situacao                    INT,

    data_primeira_interacao     VARCHAR(20),
    data_ultima_alteracao       VARCHAR(20),

    quantidade_interacao_publico INT,
    quantidade_interacao_interno INT,

    criado_em                   DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em               DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_chamado (tenant_id, codigo)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;