import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "pessoa_repository")

# ==========================================
# SILVER — pessoa_bi
# ==========================================

def upsert_pessoa_bi(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela pessoa_bi.
    Usa codigo_pessoa como chave única.
    """
    if not registros:
        logger.warning("upsert_pessoa_bi chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            codigo_pessoa = item.get("codigo_pessoa")

            if not codigo_pessoa:
                continue

            cursor.execute(
                "SELECT codigo_pessoa FROM pessoa_bi WHERE codigo_pessoa = %s",
                (codigo_pessoa,),
            )
            existe = cursor.fetchone()

            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_pessoa"]

            sql = f"""
                INSERT INTO pessoa_bi ({', '.join(colunas)})
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
                logger.error(f"Erro upsert pessoa_bi codigo={codigo_pessoa}: {e}")

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(f"pessoa_bi | INSERT={inseridos} UPDATE={atualizados} ERRO={erros}")

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }