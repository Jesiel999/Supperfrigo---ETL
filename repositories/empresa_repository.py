import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "pessoa_repository")

# ==========================================
# SILVER — slv_empresa
# ==========================================

def upsert_slv_empresa(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela slv_empresa.
    Usa codigo_empresa como chave única.
    """
    if not registros:
        # logger.warning("upsert_slv_empresa chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            codigo_empresa = item.get("codigo_empresa")

            if not codigo_empresa:
                continue

            cursor.execute(
                "SELECT codigo_empresa FROM slv_empresa WHERE codigo_empresa = %s",
                (codigo_empresa,),
            )
            existe = cursor.fetchone()

            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_empresa"]

            sql = f"""
                INSERT INTO slv_empresa ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)

                cursor.execute(sql, item)

                if existe:
                    atualizados += 1
                else:
                    inseridos += 1

            except Exception as e:
                conn.rollback()
                erros += 1
                logger.error(f"Erro upsert slv_empresa codigo={codigo_empresa}: {e}")

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    # logger.info(f"slv_empresa | INSERT={inseridos} UPDATE={atualizados} ERRO={erros}")

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }