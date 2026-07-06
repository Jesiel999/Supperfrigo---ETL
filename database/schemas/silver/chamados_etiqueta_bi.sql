CREATE TABLE IF NOT EXISTS chamados_etiqueta_bi (

    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,

    empresa_id          INT,

    chamado_codigo      INT,

    etiqueta_id         INT
);