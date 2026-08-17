CREATE TABLE IF NOT EXISTS pessoa_sances_raw (
    codigo_cliente INT PRIMARY KEY,
    tipo VARCHAR(10),
    cpf_cnpj VARCHAR(255),
    nome_cliente VARCHAR(255),
    sexo VARCHAR(30)
);