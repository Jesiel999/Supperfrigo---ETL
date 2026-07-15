CREATE TABLE IF NOT EXISTS pessoa_sances_raw (
    codigo_cliente INT PRIMARY KEY,
    tipo VARCHAR(10),
    cpf_cnpj VARCHAR(255),
    rg_ie VARCHAR(255),
    nome_cliente VARCHAR(255),
    data_nascimento VARCHAR(20),
    sexo VARCHAR(30)
);