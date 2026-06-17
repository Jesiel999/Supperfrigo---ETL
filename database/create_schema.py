from database.mysql_connection import connection_mysql

conn = connection_mysql()
cursor = conn.cursor()

arquivos = [
    "database/schemas/bronze/financeiro_raw.sql",
    "database/schemas/silver/pessoa_bi.sql",
    "database/schemas/silver/empresa_bi.sql",
    "database/schemas/silver/financeiro_bi.sql",
    "database/schemas/gold/inadimplencia_gold.sql",
    "gold/views/vw_bi_inadimplencia.sql",
    "database/schemas/gold/pmp_gold.sql",
    "database/schemas/gold/pmr_gold.sql",
]

for arquivo in arquivos:

    with open(arquivo, "r", encoding="utf-8") as f:
        sql = f.read()

    for comando in sql.split(";"):

        comando = comando.strip()

        if comando:
            cursor.execute(comando)

conn.commit()

cursor.close()
conn.close()

print("Schemas instalados com sucesso")