CREATE TABLE IF NOT EXISTS campoAdicional_sults_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,

    pessoa_id INT NOT NULL,

    valor VARCHAR(20),
    id_campoAdicional INT,
    label VARCHAR(100),

    CONSTRAINT fk_campoadicional_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sults_raw(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_campoadicional_pessoa
ON campoAdicional_sults_raw(pessoa_id);