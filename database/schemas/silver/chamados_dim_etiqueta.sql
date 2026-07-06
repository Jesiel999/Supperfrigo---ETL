CREATE TABLE IF NOT EXISTS dim_etiqueta (

    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,

    etiqueta_id         INT,

    nome                VARCHAR(255),

    cor                 VARCHAR(20),

    UNIQUE KEY uk_etiqueta (etiqueta_id)
);