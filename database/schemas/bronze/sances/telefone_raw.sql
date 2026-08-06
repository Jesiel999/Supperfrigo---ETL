CREATE TABLE IF NOT EXISTS telefone_sances_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pessoa_id INT NOT NULL,

    celular VARCHAR(20),
    comercial VARCHAR(20),
    residencial VARCHAR(20),

    CONSTRAINT fk_telefone_sances_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sances_raw(codigo_cliente)
        ON DELETE CASCADE
);

CREATE INDEX idx_telefone_sances_pessoa
ON telefone_sances_raw(pessoa_id);
