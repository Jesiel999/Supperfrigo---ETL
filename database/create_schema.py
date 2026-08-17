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
    # Bronze
    "database/schemas/bronze/sances/estoque/precos_sances_raw.sql",
    "database/schemas/bronze/sances/estoque/produto_sances_raw.sql",
    "database/schemas/bronze/sances/estoque/quantidade_sances_raw.sql",
    "database/schemas/bronze/sances/financeiro/financeiro_raw.sql",
    "database/schemas/bronze/sances/pessoa/pessoa_raw.sql",
    "database/schemas/bronze/sances/pessoa/email_raw.sql",
    "database/schemas/bronze/sances/pessoa/endereco_raw.sql",
    "database/schemas/bronze/sances/pessoa/telefone_raw.sql",
    "database/schemas/bronze/sults/chamados/chamados_raw.sql",
    "database/schemas/bronze/sults/chamados/chamados_apoio_raw.sql",
    "database/schemas/bronze/sults/chamados/chamados_etiqueta_raw.sql",
    "database/schemas/bronze/sults/pessoa/pessoa_raw.sql",
    "database/schemas/bronze/sults/pessoa/endereco_raw.sql",
    "database/schemas/bronze/sults/pessoa/empresa_raw.sql",
    "database/schemas/bronze/sults/pessoa/campoAdicional_raw.sql",
    # SILVER
    "database/schemas/silver/chamados/chamados_bi.sql",
    "database/schemas/silver/chamados/chamados_apoio_bi.sql",
    "database/schemas/silver/chamados/chamados_departamento_bi.sql",
    "database/schemas/silver/chamados/chamados_dim_etiqueta.sql",
    "database/schemas/silver/chamados/chamados_etiqueta_bi.sql",
    "database/schemas/silver/empresa/empresa_bi.sql",
    "database/schemas/silver/estoque/estoque_empresa_bi.sql",
    "database/schemas/silver/estoque/estoque_modelo_veiculo_bi.sql",
    "database/schemas/silver/estoque/estoque_precos_bi.sql",
    "database/schemas/silver/estoque/estoque_produto_bi.sql",
    "database/schemas/silver/financeiro/financeiro_bi.sql",
    "database/schemas/silver/pessoa/pessoa_bi.sql",
    "database/schemas/silver/pessoa/endereco_bi.sql",
    "database/schemas/silver/pessoa/email_bi.sql",
    "database/schemas/silver/pessoa/colaborador_bi.sql"
    # GOLD
    "gold/views/vw_bi_inadimplencia.sql",
    "gold/views/vw_bi_receber.sql",
    "gold/views/vw_bi_pagar.sql",
    "gold/views/vm_bi_pmp.sql",
    "gold/views/vw_bi_pmr.sql",
    "gold/views/vw_bi_produto.sql",
    "gold/views/vw_bi_estoque.sql",
    "",
    "",
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