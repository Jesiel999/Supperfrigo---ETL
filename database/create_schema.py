from database.mysql_connection import connection_mysql

conn = connection_mysql()
cursor = conn.cursor()

arquivos = [
    "database/schemas/config.sql",
    "database/schemas/tenant/001_tenant.sql",
    "database/schemas/tenant/002_sistemas.sql",
    "database/schemas/tenant/003_aplicacao.sql",
    "database/schemas/tenant/004_modulo.sql",
    "database/schemas/tenant/005_permissao.sql",
    "database/schemas/tenant/006_perfil.sql",
    "database/schemas/tenant/007_usuarios.sql",
    "database/schemas/tenant/008_usuario_tenant.sql",
    "database/schemas/tenant/009_usuario_empresa.sql",
    "database/schemas/tenant/010_perfil_permissao.sql",
    "database/schemas/999_schema.sql",
    # BRONZE
    "database/schemas/bronze/sances/pos_venda/pos_venda_raw.sql",
    "database/schemas/bronze/sances/pos_venda/pos_venda_servicos_raw.sql",
    "database/schemas/bronze/sances/pos_venda/pos_venda_peca_raw.sql",
    "database/schemas/bronze/sances/pos_venda/pos_venda_nota_raw.sql",
    "database/schemas/bronze/sances/pos_venda/pos_venda_parcela_raw.sql",
    # SILVER
    "database/schemas/silver/pos_venda/pos_venda_bi.sql",
    "database/schemas/silver/pos_venda/pos_venda_peca_bi.sql",
    "database/schemas/silver/pos_venda/pos_venda_servico_bi.sql",
    "database/schemas/silver/pos_venda/pos_venda_nota_bi.sql",
    "database/schemas/silver/pos_venda/pos_venda_parcela_bi.sql",
    # GOLD
    "gold/views/vw_bi_inadimplencia.sql",
    "gold/views/vw_bi_receber.sql",
    "gold/views/vw_bi_pagar.sql",
    "gold/views/vm_bi_pmp.sql",
    "gold/views/vw_bi_pmr.sql",
    "gold/views/vw_bi_produto.sql",
    "gold/views/vw_bi_estoque.sql",
    "gold/views/vw_bi_pos_venda.sql",
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