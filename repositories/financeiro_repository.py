import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "financeiro_repository")


# ==========================================
# BRONZE — financeiro_raw
# ==========================================

def upsert_financeiro_raw(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela financeiro_raw.
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
                "SELECT codigo, data_alteracao FROM financeiro_raw WHERE codigo = %s",
                (codigo,),
            )
            existente = cursor.fetchone()

            if existente:
                if _norm(item.get("data_alteracao")) == _norm(existente.get("data_alteracao")):
                    ignorados += 1
                    continue
                acao = "UPDATE"
            else:
                acao = "INSERT"

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [f"{c}=VALUES({c})" for c in colunas if c != "codigo"]

            sql = f"""
                INSERT INTO financeiro_raw ({', '.join(colunas)})
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
        f"financeiro_raw | INSERT={inseridos} UPDATE={atualizados} "
        f"SKIP={ignorados} ERRO={erros}"
    )
    return {
        "inseridos":   inseridos,
        "atualizados": atualizados,
        "ignorados":   ignorados,
        "erros":       erros,
    }


def buscar_raw_para_transform(somente_nao_transformados: bool = True) -> list[dict]:
    """
    Retorna registros do financeiro_raw para a camada silver.

    Args:
        somente_nao_transformados:
            True  — busca apenas registros que ainda NÃO existem em financeiro_bi
                    OU que foram atualizados depois da última transformação.
                    É o modo padrão — evita reprocessar tudo a cada execução.
            False — retorna todos os registros (útil para reprocessamento forçado).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        if somente_nao_transformados:
            # LEFT JOIN: pega tudo do raw que não tem par no bi,
            # ou cujo raw.atualizado_em é mais recente que o bi.atualizado_em
            sql = """
                SELECT * FROM financeiro_raw
                ORDER BY codigo ASC 
            """
            logger.info("Buscando registros raw pendentes de transformação (LEFT JOIN)...")
        else:
            sql = "SELECT * FROM financeiro_raw ORDER BY id ASC"
            logger.info("Buscando TODOS os registros raw (reprocessamento forçado)...")

        cursor.execute(sql)
        rows = cursor.fetchall()
        logger.info(f"Raw para transformar: {len(rows)} registros encontrados.")
        return rows

    finally:
        cursor.close()
        conn.close()


# ==========================================
# SILVER — financeiro_bi
# ==========================================

def upsert_financeiro_bi(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela financeiro_bi.
    Usa codigo_raw como chave única.
    Faz commit a cada 500 registros.
    """
    if not registros:
        logger.warning("upsert_financeiro_bi chamado com lista vazia — nada a gravar.")
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
                "SELECT id FROM financeiro_bi WHERE codigo_raw = %s",
                (codigo_raw,),
            )
            existe = cursor.fetchone()

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_raw"]

            sql = f"""
                INSERT INTO financeiro_bi ({', '.join(colunas)})
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
        f"financeiro_bi | INSERT={inseridos} UPDATE={atualizados} ERRO={erros}"
    )
    return {"inseridos": inseridos, "atualizados": atualizados, "erros": erros}


# ==========================================
# GOLD — inadimplencia_gold
# ==========================================

def upsert_inadimplencia_gold(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela inadimplencia_gold.
    Antes de inserir, limpa os registros antigos da tabela
    para refletir sempre o estado atual (TRUNCATE + INSERT).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    inseridos = erros = 0

    try:
        # Limpa a tabela gold antes de recarregar
        # Garante que registros que saíram da inadimplência somam fora
        cursor.execute("TRUNCATE TABLE inadimplencia_gold")
        logger.info("inadimplencia_gold truncada para recarga completa.")

        for item in registros:
            if not item:
                continue

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            sql = f"""
                INSERT INTO inadimplencia_gold ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
            """

            try:
                cursor.execute(sql, item)
                inseridos += 1
            except Exception as e:
                erros += 1
                logger.error(f"Erro insert inadimplencia_gold: {e} | item={item}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro crítico upsert_inadimplencia_gold: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    logger.info(f"inadimplencia_gold | INSERT={inseridos} ERRO={erros}")
    return {"inseridos": inseridos, "erros": erros}


def buscar_bi_para_inadimplencia_gold() -> list[dict]:
    """
    Retorna registros do financeiro_bi para a camada gold.
    Traz títulos a RECEBER vencidos ou em aberto com vencimento anterior a hoje.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM financeiro_bi
            WHERE tipo_titulo = 'RECEBER'
              AND status_financeiro IN ('VENCIDO', 'EM ABERTO', 'PAGO')
            ORDER BY data_vencimento ASC
        """)
        rows = cursor.fetchall()
        logger.info(f"financeiro_bi  gold: {len(rows)} registros inadimplentes encontrados.")
        return rows

    finally:
        cursor.close()
        conn.close()


# ==========================================
# GOLD — pmp_gold
# ==========================================

def upsert_pmp_gold(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela pmp_gold.
    Antes de inserir, limpa os registros antigos da tabela
    para refletir sempre o estado atual (TRUNCATE + INSERT).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    inseridos = erros = 0

    try:
        # Limpa a tabela gold antes de recarregar
        # Garante que registros que saíram da inadimplência somam fora
        cursor.execute("TRUNCATE TABLE pmp_gold")
        logger.info("pmp_gold truncada para recarga completa.")

        for item in registros:
            if not item:
                continue

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            sql = f"""
                INSERT INTO pmp_gold ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
            """

            try:
                cursor.execute(sql, item)
                inseridos += 1
            except Exception as e:
                erros += 1
                logger.error(f"Erro insert pmp_gold: {e} | item={item}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro crítico upsert_pmp_gold: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    logger.info(f"pmp_gold | INSERT={inseridos} ERRO={erros}")
    return {"inseridos": inseridos, "erros": erros}


def buscar_bi_para_pmp_gold() -> list[dict]:
    """
    Retorna registros do financeiro_bi para a camada gold.
    Traz títulos a PAGAR PAGOS.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM financeiro_bi
            WHERE tipo_titulo = 'PAGAR'
                AND status_financeiro IN ('PAGO')
            ORDER BY codigo_raw ASC
        """)
        rows = cursor.fetchall()
        logger.info(f"financeiro_bi  gold: {len(rows)} registros prazo medio de pagamento encontrados.")
        return rows

    finally:
        cursor.close()
        conn.close()

# ==========================================
# GOLD — pmr_gold
# ==========================================

def upsert_pmr_gold(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela pmr_gold.
    Antes de inserir, limpa os registros antigos da tabela
    para refletir sempre o estado atual (TRUNCATE + INSERT).
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    inseridos = erros = 0

    try:
        # Limpa a tabela gold antes de recarregar
        # Garante que registros que saíram da inadimplência somam fora
        cursor.execute("TRUNCATE TABLE pmr_gold")
        logger.info("pmr_gold truncada para recarga completa.")

        for item in registros:
            if not item:
                continue

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]

            sql = f"""
                INSERT INTO pmr_gold ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
            """

            try:
                cursor.execute(sql, item)
                inseridos += 1
            except Exception as e:
                erros += 1
                logger.error(f"Erro insert pmr_gold: {e} | item={item}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro crítico upsert_pmr_gold: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

    logger.info(f"pmr_gold | INSERT={inseridos} ERRO={erros}")
    return {"inseridos": inseridos, "erros": erros}


def buscar_bi_para_pmr_gold() -> list[dict]:
    """
    Retorna registros do financeiro_bi para a camada gold.
    Traz títulos a RECEBER PAGOS.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM financeiro_bi
            WHERE tipo_titulo = 'RECEBER'
                AND status_financeiro IN ('PAGO')
            ORDER BY codigo_raw ASC
        """)
        rows = cursor.fetchall()
        logger.info(f"financeiro_bi  gold: {len(rows)} registros prazo medio de recebimento encontrados.")
        return rows

    finally:
        cursor.close()
        conn.close()