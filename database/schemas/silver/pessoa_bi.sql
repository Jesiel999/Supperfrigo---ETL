CREATE TABLE IF NOT EXISTS pessoa_bi (

    id INT AUTO_INCREMENT PRIMARY KEY,

    id_sances INT NULL,
    id_sults INT NULL,
    id_multisys INT NULL,
    id_meta INT NULL,
    id_econnect INT NULL,

    nome VARCHAR(255),
    sexo VARCHAR(1),
    data_nascimento DATE,

    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_sances(id_sances),
    UNIQUE KEY uk_sults(id_sults),

    INDEX idx_nome(nome),
    INDEX idx_cpf(id_sances,id_sults)
);