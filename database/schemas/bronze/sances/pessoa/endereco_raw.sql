CREATE TABLE IF NOT EXISTS endereco_sances_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pessoa_id INT NOT NULL,

    rua VARCHAR(255),
    numero VARCHAR(50),
    complemento VARCHAR(255),
    bairro VARCHAR(255),
    cidade VARCHAR(100),
    uf VARCHAR(10),
    cep VARCHAR(10),

    CONSTRAINT fk_endereco_sances_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sances_raw(codigo_cliente)
        ON DELETE CASCADE
);

CREATE INDEX idx_endereco_sances_pessoa
ON endereco_sances_raw(pessoa_id);
