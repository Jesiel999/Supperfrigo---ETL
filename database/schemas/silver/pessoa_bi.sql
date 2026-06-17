CREATE TABLE IF NOT EXISTS pessoa_bi (
    codigo_pessoa INT NOT NULL,
    nome_pessoa   VARCHAR(255) NOT NULL,

    CONSTRAINT pk_pessoa_bi PRIMARY KEY (codigo_pessoa)
);