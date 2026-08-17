CREATE TABLE IF NOT EXISTS dim_departamento (

    id              BIGINT AUTO_INCREMENT PRIMARY KEY,

    empresa_id      INT,

    departamento_id INT,

    nome            VARCHAR(100),

    UNIQUE KEY uk_departamento (empresa_id, departamento_id)
);