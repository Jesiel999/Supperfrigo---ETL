from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("repository", "chamados_apoio_repository")


def upsert_chamados_apoio_raw(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_apoio_raw.

    Chave única: tenant_id + chamado_codigo + pessoa_id + departamento_id
    """

    if not registros:
        logger.warning("upsert_chamados_apoio_raw chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True, buffered=True)

    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in (
                    "tenant_id",
                    "chamado_codigo",
                    "pessoa_id",
                    "departamento_id",
                )
            ]

            sql = f"""
                INSERT INTO chamados_apoio_raw
                ({', '.join(colunas)})
                VALUES
                ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates) if updates else "tenant_id=tenant_id"}
            """

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)

                cursor.execute(sql, item)

                # mysql-connector geralmente retorna:
                if cursor.rowcount == 1:
                    inseridos += 1
                elif cursor.rowcount == 2:
                    atualizados += 1
                else:
                    # fallback caso o conector retorne algo diferente
                    atualizados += 1

            except Exception as e:
                conn.rollback()
                erros += 1

                logger.error(
                    f"Erro upsert apoio chamado={item.get('chamado_codigo')} "
                    f"pessoa={item.get('pessoa_id')}: {e}"
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial apoio_raw: {i} registros processados")

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(
        f"chamados_apoio_raw | "
        f"INSERT={inseridos} "
        f"UPDATE={atualizados} "
        f"ERRO={erros}"
    )

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }

def upsert_chamados_apoio_bi(registros: list[dict]) -> dict:
    if not registros:
        logger.warning("upsert_chamados_apoio_bi chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            cursor.execute(
                """
                SELECT id
                FROM chamados_apoio_bi
                WHERE chamado_codigo = %s
                  AND pessoa_id = %s
                  AND departamento_id <=> %s
                """,
                (
                    item.get("chamado_codigo"),
                    item.get("pessoa_id"),
                    item.get("departamento_id"),
                ),
            )
            existe = cursor.fetchone()

            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in ("chamado_codigo", "pessoa_id", "departamento_id")
            ]

            sql = f"""
                INSERT INTO chamados_apoio_bi
                ({', '.join(colunas)})
                VALUES
                ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates) if updates else "tenant_id=tenant_id"}
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
                logger.error(
                    f"Erro upsert apoio_bi chamado={item.get('chamado_codigo')} "
                    f"pessoa={item.get('pessoa_id')} depto={item.get('departamento_id')}: {e}"
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(
        f"chamados_apoio_bi | INSERT={inseridos} UPDATE={atualizados} ERRO={erros}"
    )

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }
    """
    Insere ou atualiza registros na tabela chamados_apoio_bi.

    Chave única: chamado_codigo + pessoa_id
    """

    if not registros:
        logger.warning("upsert_chamados_apoio_bi chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True, buffered=True)

    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in ("chamado_codigo", "pessoa_id")
            ]

            sql = f"""
                INSERT INTO chamados_apoio_bi
                ({', '.join(colunas)})
                VALUES
                ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates) if updates else "chamado_codigo=chamado_codigo"}
            """

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)

                cursor.execute(sql, item)

                if cursor.rowcount == 1:
                    inseridos += 1
                elif cursor.rowcount == 2:
                    atualizados += 1
                else:
                    atualizados += 1

            except Exception as e:
                conn.rollback()
                erros += 1

                logger.error(
                    f"Erro upsert apoio_bi chamado={item.get('chamado_codigo')}: {e}"
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial apoio_bi: {i} registros processados")

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(
        f"chamados_apoio_bi | "
        f"INSERT={inseridos} "
        f"UPDATE={atualizados} "
        f"ERRO={erros}"
    )

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }