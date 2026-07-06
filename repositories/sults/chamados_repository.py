import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "chamados_repository")


# ==========================================
# BRONZE — chamados_raw
# ==========================================

def upsert_chamados_raw(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_raw.
    Compara data_alteracao para decidir se atualiza.
    Faz commit a cada 500 registros para não travar memória.
    """
    if not registros:
        return {"inseridos": 0, "atualizados": 0, "ignorados": 0, "erros": 0}

    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos   = 0
    atualizados = 0
    ignorados   = 0
    erros       = 0
    BATCH_COMMIT = 500

    def _norm(valor) -> str:
        if valor is None:
            return ""
        return str(valor).strip()

    try:
        for i, item in enumerate(registros, start=1):
            codigo = item.get("codigo")
            if not codigo:
                ignorados += 1
                continue

            # Verifica existência pelo codigo (chave única)
            cursor.execute(
                """
                SELECT codigo, data_ultima_alteracao
                FROM chamados_raw
                WHERE tenant_id = %s AND codigo = %s
                """,
                (item["tenant_id"], codigo),
            )
            existente = cursor.fetchone()

            if existente:
                if _norm(item.get("data_ultima_alteracao")) == _norm(existente.get("data_ultima_alteracao")):
                    ignorados += 1
                    continue
                acao = "UPDATE"
            else:
                acao = "INSERT"

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [f"{c}=VALUES({c})" for c in colunas if c != "codigo"]

            sql = f"""
                INSERT INTO chamados_raw ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)

                cursor.execute(sql, item)

                if acao == "INSERT":
                    inseridos += 1
                else:
                    atualizados += 1

            except Exception as e:
                conn.rollback()
                erros += 1
                logger.error(f"Erro upsert raw codigo={codigo}: {e}")

            # Commit parcial a cada BATCH_COMMIT registros
            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial raw: {i} registros processados")

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(
        f"chamados_raw | INSERT={inseridos} UPDATE={atualizados} "
        f"SKIP={ignorados} ERRO={erros}"
    )
    return {
        "inseridos":   inseridos,
        "atualizados": atualizados,
        "ignorados":   ignorados,
        "erros":       erros,
    }


def buscar_raw_para_transform(somente_nao_transformados: bool = True) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        logger.warning("### ENTREI NO buscar_raw_para_transform NOVO ###")

        cursor.execute("SELECT DATABASE() AS banco")
        logger.warning(f"### DATABASE(): {cursor.fetchone()} ###")

        cursor.execute("SELECT COUNT(*) AS total FROM chamados_raw")
        logger.warning(f"### COUNT chamados_raw: {cursor.fetchone()} ###")

        cursor.execute("""
            SELECT MIN(codigo) AS min_codigo, MAX(codigo) AS max_codigo
            FROM chamados_raw
        """)
        logger.warning(f"### RANGE chamados_raw: {cursor.fetchone()} ###")

        sql = """
            SELECT *
            FROM chamados_raw
            ORDER BY codigo ASC
        """
        logger.warning(f"### SQL EXECUTADO: {sql} ###")

        cursor.execute(sql)
        rows = cursor.fetchall()
        logger.warning(f"### TOTAL ROWS RAW: {len(rows)} ###")

        return rows

    finally:
        cursor.close()
        conn.close()
# ==========================================
# SILVER — chamados_bi
# ==========================================

def upsert_chamados_bi(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_bi.
    Usa codigo_raw como chave única.
    Faz commit a cada 500 registros.
    """
    if not registros:
        logger.warning("upsert_chamados_bi chamado com lista vazia — nada a gravar.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}

    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    inseridos   = 0
    atualizados = 0
    erros       = 0
    BATCH_COMMIT = 500

    try:
        for i, item in enumerate(registros, start=1):
            codigo_raw = item.get("codigo_raw")
            if not codigo_raw:
                logger.warning(f"Registro sem codigo_raw — ignorado: {item}")
                continue

            # Verifica se já existe para contar corretamente INSERT vs UPDATE
            cursor.execute(
                "SELECT id FROM chamados_bi WHERE codigo_raw = %s",
                (codigo_raw,),
            )
            existe = cursor.fetchone()

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_raw"]

            sql = f"""
                INSERT INTO chamados_bi ({', '.join(colunas)})
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
                logger.error(f"Erro upsert bi codigo_raw={codigo_raw}: {e}")

            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial bi: {i} registros processados")

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    logger.info(
        f"chamados_bi | INSERT={inseridos} UPDATE={atualizados} ERRO={erros}"
    )
    return {"inseridos": inseridos, "atualizados": atualizados, "erros": erros}


# ==========================================
# GOLD — chamados geral
# ==========================================

def upsert_chamados_geral_gold(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_geral_gold.
    Antes de inserir, limpa os registros antigos da tabela
    para refletir sempre o estado atual (TRUNCATE + INSERT).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    inseridos = erros = 0

    try:
        # Limpa a tabela gold antes de recarregar
        # Garante que registros que saíram da inadimplência somam fora
        cursor.execute("TRUNCATE TABLE chamados_geral_gold")
        logger.info("chamados_geral_gold truncada para recarga completa.")

        for item in registros:
            if not item:
                continue

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            sql = f"""
                INSERT INTO chamados_geral_gold ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
            """

            try:
                cursor.execute(sql, item)
                inseridos += 1
            except Exception as e:
                erros += 1
                logger.error(f"Erro insert chamados_geral_gold: {e} | item={item}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro crítico upsert_chamados_geral_gold: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    logger.info(f"chamados_geral_gold | INSERT={inseridos} ERRO={erros}")
    return {"inseridos": inseridos, "erros": erros}


def buscar_bi_para_chamados_geral_gold() -> list[dict]:
    """
    Retorna registros do chamados_bi para a camada gold.
    Traz títulos a RECEBER vencidos ou em aberto com vencimento anterior a hoje.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM chamados_bi
            ORDER BY data_aberto ASC
        """)
        rows = cursor.fetchall()
        logger.info(f"chamados_bi  gold: {len(rows)} registros chamados encontrados.")
        return rows

    finally:
        cursor.close()
        conn.close()

