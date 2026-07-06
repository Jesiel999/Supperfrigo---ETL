CREATE TABLE IF NOT EXISTS chamados_bi (

    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,

    codigo_raw              INT NOT NULL,

    titulo                  TEXT,

    tipo                    INT,
    situacao                INT,

    solicitante_id          INT,
    responsavel_id          INT,

    unidade_id              INT,

    departamento_id         INT,

    departamento_envio_id   INT,

    assunto_id              INT,

    data_aberto             DATETIME,
    data_resolvido          DATETIME,
    data_concluido          DATETIME,
    data_resolver_planejado DATETIME,
    data_resolver_estipulado DATETIME,

    data_primeira_interacao DATETIME,
    data_ultima_alteracao   DATETIME,

    avaliacao_nota          INT,
    avaliacao_observacao    TEXT,

    quantidade_interacao_publico INT,
    quantidade_interacao_interno INT,

    -- Campos calculados
    tempo_primeira_resposta INT,
    tempo_resolucao         INT,
    sla_horas               DECIMAL(10,2),
    sla_cumprido            BOOLEAN,

    horas_atrasado          DECIMAL(10,2),
    horas_resolver          DECIMAL(10,2),

    tipo_solicitacao        VARCHAR(100),


    criado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em           DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_chamado (codigo)
);