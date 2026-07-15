CREATE TABLE IF NOT EXISTS pessoa_sults_raw (
    id INT PRIMARY KEY,

    nome VARCHAR(255),
    ativo BOOLEAN,
    sexo VARCHAR(1),
    cpf VARCHAR(255),
    numeroIdentidade VARCHAR(255),
    dtNascimento VARCHAR(20),

    celular VARCHAR(100),
    telefone VARCHAR(100),
    email VARCHAR(100),

    dtCadastro VARCHAR(30),
    dtUltimaAlteracao VARCHAR(30),
    dtInativacao VARCHAR(30),

    thumbnail VARCHAR(100),
    estadoCivil VARCHAR(30),
    nivelEscolaridade VARCHAR(30)
);