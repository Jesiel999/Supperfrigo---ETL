import logging
from datetime import datetime
from database.mysql_connection import connection_mysql
from repositories.sances.pos_venda_repository import marcar_processado

logger = logging.getLogger(__name__)


def upsert_telemetria_raw(tenant_id: int, registros: list[dict]) -> dict:
    """
    Insere registros em telemetria_raw. Usa (tenant_id, veiculo_id, data_evento)
    como chave de deduplicação — se o mesmo evento já foi gravado numa
    execução anterior (snapshot repetido sem evento novo), é ignorado.

    REQUER: índice único em (tenant_id, veiculo_id, data_evento).
    """
    if not registros:
        return {"inseridos": 0, "ignorados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor()

    inseridos = 0
    ignorados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            item["tenant_id"] = tenant_id

            if item.get("data_evento") is None or item.get("veiculo_id") is None:
                ignorados += 1
                continue

            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            sql = f"""
                INSERT IGNORE INTO telemetria_raw ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
            """

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)
                cursor.execute(sql, item)
                if cursor.rowcount == 1:
                    inseridos += 1
                else:
                    ignorados += 1  # já existia (índice único bateu)
            except Exception as e:
                conn.rollback()
                erros += 1
                # logger.error(f"Erro ao inserir telemetria_raw veiculo_id={item.get('veiculo_id')}: {e}")

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    # logger.info(f"telemetria_raw | INSERT={inseridos} IGNORADOS={ignorados} ERRO={erros}")
    return {"inseridos": inseridos, "ignorados": ignorados, "erros": erros}


def buscar_raw_pendentes(tenant_id: int, limite: int = 1000) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM telemetria_raw
        WHERE tenant_id = %s AND processado = FALSE
        ORDER BY id
        LIMIT %s
        """,
        (tenant_id, limite),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def marcar_processado(ids: list[int]) -> None:
    if not ids:
        return
    conn = connection_mysql()
    cursor = conn.cursor()
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"UPDATE telemetria_raw SET processado = TRUE, data_processamento = NOW(3) WHERE id IN ({placeholders})",
        tuple(ids),
    )
    conn.commit()
    cursor.close()
    conn.close()