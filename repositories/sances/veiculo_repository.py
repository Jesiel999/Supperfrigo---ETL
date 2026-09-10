from database.mysql_connection import connection_mysql

def garantir_veiculo_stub(tenant_id: int, veiculo_id: int) -> None:
    """
    Garante que exista uma linha em veiculo_bi com este id. Se não existir,
    cria um stub mínimo — o pipeline de pós-venda Sances completa os
    demais campos (placa, modelo, cor) quando processar esse veículo.
    Não sobrescreve dados já existentes.
    """
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT IGNORE INTO veiculo_bi (id, tenant_id, codigo_econnect)
            VALUES (%s, %s, %s)
            """,
            (veiculo_id, tenant_id, veiculo_id),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()