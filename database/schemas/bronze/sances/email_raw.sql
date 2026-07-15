
CREATE TABLE email_sances_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pessoa_id INT NOT NULL,
    email VARCHAR(500),

    CONSTRAINT fk_email_sances_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_sances_raw(codigo_cliente)
        ON DELETE CASCADE
);

CREATE INDEX idx_email_sances_pessoa
ON email_sances_raw(pessoa_id);
