CREATE TABLE IF NOT EXISTS endereco_sults_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,

    pessoa_id INT NOT NULL,

    uf VARCHAR(10),
    cidade VARCHAR(100),
    complemento VARCHAR(255),
    numero VARCHAR(50),
    bairro VARCHAR(255),
    cep VARCHAR(10),
    rua VARCHAR(255),

    CONSTRAINT fk_endereco_sults_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sults_raw(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_endereco_sults_pessoa
ON endereco_sults_raw(pessoa_id);

