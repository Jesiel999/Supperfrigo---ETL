CREATE TABLE IF NOT EXISTS empresa_bi (
    codigo_empresa INT NOT NULL,
    nome_empresa   VARCHAR(255) NOT NULL,

    CONSTRAINT pk_empresa_bi PRIMARY KEY (codigo_empresa)
);