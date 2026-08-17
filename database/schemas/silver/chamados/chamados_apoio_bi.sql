CREATE TABLE IF NOT EXISTS chamados_apoio_bi (

    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,

    empresa_id          INT,

    chamado_codigo      INT,

    pessoa_id           INT,

    departamento_id     INT,

    pessoa_unidade      BOOLEAN
);