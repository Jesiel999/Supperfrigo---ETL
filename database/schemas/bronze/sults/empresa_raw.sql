CREATE TABLE IF NOT EXISTS empresa_sults_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,

    pessoa_id INT NOT NULL,

    qualificacao_nome VARCHAR(100),
    qualificacao_id INT,

    nomeFantasia_id INT,
    nomeFantasia_cargo_nome VARCHAR(100),
    nomeFantasia_cargo_id INT,

    CONSTRAINT fk_empresa_sults_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sults_raw(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_empresa_sults_pessoa
ON empresa_sults_raw(pessoa_id);
