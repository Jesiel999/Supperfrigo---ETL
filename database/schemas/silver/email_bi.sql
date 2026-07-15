CREATE TABLE IF NOT EXISTS email_bi (

    id INT AUTO_INCREMENT PRIMARY KEY,

    pessoa_id INT NOT NULL,

    email VARCHAR(500),

    CONSTRAINT fk_email_bi
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_bi(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_email_bi_pessoa
ON email_bi(pessoa_id);

