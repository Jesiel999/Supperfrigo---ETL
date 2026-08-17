CREATE TABLE IF NOT EXISTS colaborador_bi (

    id INT AUTO_INCREMENT PRIMARY KEY,

    empresa_id INT NOT NULL,
    pessoa_id INT NOT NULL,

    CONSTRAINT fk_colaborador_pessoa
        FOREIGN KEY (pessoa_id)
        REFERENCES pessoa_bi(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_colaborador_empresa
ON colaborador_bi(empresa_id);

CREATE INDEX idx_colaborador_pessoa
ON colaborador_bi(pessoa_id);