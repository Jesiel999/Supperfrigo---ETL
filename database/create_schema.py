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
    "database/schemas/bronze/sances/pessoa_raw.sql",
    "database/schemas/bronze/sults/pessoa_raw.sql",
    "database/schemas/bronze/sances/email_raw.sql",
    "database/schemas/bronze/sults/endereco_raw.sql",
    "database/schemas/bronze/sances/endereco_raw.sql",
    "database/schemas/bronze/sults/empresa_raw.sql",
    "database/schemas/bronze/sults/campoAdicional_raw.sql",
    "database/schemas/silver/pessoa_bi.sql",
    "database/schemas/silver/endereco_bi.sql",
    "database/schemas/silver/email_bi.sql",
    "database/schemas/silver/colaborador_bi.sql",
    "database/schemas/sances/bronze/financeiro_raw.sql",
    "database/schemas/silver/pessoa_bi.sql",
    "database/schemas/silver/empresa_bi.sql",
    "database/schemas/silver/financeiro_bi.sql",
    "database/schemas/gold/inadimplencia_gold.sql",
    "gold/views/vw_bi_inadimplencia.sql",
    "database/schemas/gold/pmp_gold.sql",
    "database/schemas/gold/pmr_gold.sql",
    "database/schemas/sults/bronze/chamados_apoio_raw.sql",
    "database/schemas/sults/bronze/chamados_etiqueta_raw.sql",
    "database/schemas/sults/bronze/chamados_raw.sql",
    "database/schemas/silver/chamados_apoio_bi.sql",
    "database/schemas/silver/chamados_bi.sql",
    "database/schemas/silver/chamados_departamento_bi.sql",
    "database/schemas/silver/chamados_dim_etiqueta.sql",
    "database/schemas/silver/chamados_etiqueta_bi.sql",
    "database/schemas/gold/chamados_geral_gold.sql",
    "gold/views/vw_bi_chamados_geral.sql",
    "gold/views/vm_bi_pmp.sql",
    "gold/views/vw_bi_pmr.sql",
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