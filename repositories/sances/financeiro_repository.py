import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger
from datetime import datetime

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

    def converter_data(valor):
        if valor is None:
            return None

        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return None

            formatos = (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            )

            for formato in formatos:
                try:
                    return datetime.strptime(valor, formato)
                except ValueError:
                    pass

        return None


    def data_maior(data_nova, data_banco):
        data_nova = converter_data(data_nova)
        data_banco = converter_data(data_banco)

        if data_nova is None:
            return False

        if data_banco is None:
            return True

        return data_nova > data_banco
    
    def situacao(situacao_nova, situacao_antiga):

        if situacao_nova is None:
            return False
        
        if situacao_antiga is None:
            return True
        
        return situacao_nova != situacao_antiga
    

    try:
        for i, item in enumerate(registros, start=1):
            codigo = item.get("codigo")
            if not codigo:
                ignorados += 1
                continue

            # Verifica existência pelo codigo (chave única)
            cursor.execute(
                "SELECT codigo, data_alteracao, data_baixa, data_insercao, codigo_situacao FROM financeiro_raw WHERE codigo = %s",
                (codigo,),
            )
            existente = cursor.fetchone()

            if existente:
                
                atualizar = (
                    data_maior(item.get("data_alteracao"), existente.get("data_alteracao")) or
                    data_maior(item.get("data_baixa"), existente.get("data_baixa")) or
                    data_maior(item.get("data_insercao"), existente.get("data_insercao")) or
                    situacao(item.get("codigo_situacao"), existente.get("codigo_situacao"))

                )

                if not atualizar:
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
            sql = """
                SELECT * FROM financeiro_raw                    
            """
            logger.info("Buscando registros raw pendentes de transformação (LEFT JOIN)...")
        else:
            sql = "SELECT * FROM financeiro_raw ORDER BY codigo ASC"
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

    def converter_data(valor):
        if valor is None:
            return None

        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return None

            formatos = (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            )

            for formato in formatos:
                try:
                    return datetime.strptime(valor, formato)
                except ValueError:
                    pass

        return None


    def data_maior(data_nova, data_banco):
        data_nova = converter_data(data_nova)
        data_banco = converter_data(data_banco)

        if data_nova is None:
            return False

        if data_banco is None:
            return True

        return data_nova > data_banco
    
    def situacao(situacao_nova, situacao_antiga):

        if situacao_nova is None:
            return False
        
        if situacao_antiga is None:
            return True
        
        return situacao_nova != situacao_antiga
    
    try:
        for i, item in enumerate(registros, start=1):
            codigo_raw = item.get("codigo_raw")
            if not codigo_raw:
                logger.warning(f"Registro sem codigo_raw — ignorado: {item}")
                continue

            # Verifica existência pelo codigo (chave única)
            cursor.execute("""
                SELECT
                    atualizado_em,
                    data_baixa,
                    codigo_situacao
                FROM financeiro_bi
                WHERE codigo_raw = %s
            """, (codigo_raw,))

            
            existente = cursor.fetchone()

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

                if existente:
                
                    atualizar = (
                        data_maior(item.get("data_alteracao"), existente.get("atualizado_em")) or
                        data_maior(item.get("data_baixa"), existente.get("data_baixa")) or
                        situacao(item.get("codigo_situacao"), existente.get("codigo_situacao"))
                    )

                    if not atualizar:
                        atualizados += 1
                        continue
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

