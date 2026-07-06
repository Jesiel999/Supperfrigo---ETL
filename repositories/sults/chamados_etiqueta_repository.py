from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("repository", "chamados_etiqueta_repository")


# ==========================================
# BRONZE — chamados_etiqueta_raw
# ==========================================

def upsert_chamados_etiqueta_raw(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_etiqueta_raw.
    
    Chave única: tenant_id + chamado_codigo + etiqueta_id
    
    Args:
        registros: Lista de dicionários com dados de etiqueta
        
    Returns:
        Dict com contagem de inseridos, atualizados e erros
    """
    
    if not registros:
        logger.warning("upsert_chamados_etiqueta_raw chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500
    
    try:
        
        for i, item in enumerate(registros, start=1):
            
            # Verifica existência pela chave única
            cursor.execute(
                """
                SELECT id
                FROM chamados_etiqueta_raw
                WHERE tenant_id=%s
                  AND chamado_codigo=%s
                  AND etiqueta_id=%s
                """,
                (
                    item.get("tenant_id"),
                    item.get("chamado_codigo"),
                    item.get("etiqueta_id"),
                ),
            )
            
            existe = cursor.fetchone()
            
            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            
            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in (
                    "tenant_id",
                    "chamado_codigo",
                    "etiqueta_id",
                )
            ]
            
            sql = f"""
                INSERT INTO chamados_etiqueta_raw
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
                    f"Erro upsert etiqueta_raw chamado={item.get('chamado_codigo')} "
                    f"etiqueta={item.get('etiqueta_id')}: {e}"
                )
            
            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial etiqueta_raw: {i} registros processados")
        
        conn.commit()
    
    finally:
        cursor.close()
        conn.close()
    
    logger.info(
        f"chamados_etiqueta_raw | "
        f"INSERT={inseridos} "
        f"UPDATE={atualizados} "
        f"ERRO={erros}"
    )
    
    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }


# ==========================================
# DIMENSÃO — dim_etiqueta
# ==========================================

def upsert_dim_etiqueta(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela dim_etiqueta.
    Tabela de dimensão para deduplicação de etiquetas.
    
    Chave única: etiqueta_id
    
    Args:
        registros: Lista com {etiqueta_id, nome, cor}
        
    Returns:
        Dict com contagem de inseridos, atualizados e erros
    """
    
    if not registros:
        logger.warning("upsert_dim_etiqueta chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    inseridos = 0
    atualizados = 0
    erros = 0
    
    try:
        
        for item in registros:
            
            # Verifica existência
            cursor.execute(
                "SELECT id FROM dim_etiqueta WHERE etiqueta_id=%s",
                (item.get("etiqueta_id"),),
            )
            
            existe = cursor.fetchone()
            
            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            
            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c != "etiqueta_id"
            ]
            
            sql = f"""
                INSERT INTO dim_etiqueta
                ({', '.join(colunas)})
                VALUES
                ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates) if updates else "etiqueta_id=etiqueta_id"}
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
                    f"Erro upsert dim_etiqueta etiqueta_id={item.get('etiqueta_id')}: {e}"
                )
        
        conn.commit()
    
    finally:
        cursor.close()
        conn.close()
    
    logger.info(
        f"dim_etiqueta | "
        f"INSERT={inseridos} "
        f"UPDATE={atualizados} "
        f"ERRO={erros}"
    )
    
    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }


# ==========================================
# SILVER — chamados_etiqueta_bi
# ==========================================

def upsert_chamados_etiqueta_bi(registros: list[dict]) -> dict:
    """
    Insere ou atualiza registros na tabela chamados_etiqueta_bi (fato).
    
    Chave única: chamado_codigo + etiqueta_id
    
    Args:
        registros: Lista de dicionários com chamado_codigo e etiqueta_id
        
    Returns:
        Dict com contagem de inseridos, atualizados e erros
    """
    
    if not registros:
        logger.warning("upsert_chamados_etiqueta_bi chamado com lista vazia.")
        return {"inseridos": 0, "atualizados": 0, "erros": 0}
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    inseridos = 0
    atualizados = 0
    erros = 0
    BATCH_COMMIT = 500
    
    try:
        
        for i, item in enumerate(registros, start=1):
            
            # Verifica existência
            cursor.execute(
                """
                SELECT id
                FROM chamados_etiqueta_bi
                WHERE chamado_codigo=%s
                  AND etiqueta_id=%s
                """,
                (
                    item.get("chamado_codigo"),
                    item.get("etiqueta_id"),
                ),
            )
            
            existe = cursor.fetchone()
            
            colunas = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            
            updates = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in ("chamado_codigo", "etiqueta_id")
            ]
            
            sql = f"""
                INSERT INTO chamados_etiqueta_bi
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
                
                if existe:
                    atualizados += 1
                else:
                    inseridos += 1
            
            except Exception as e:
                
                conn.rollback()
                erros += 1
                
                logger.error(
                    f"Erro upsert etiqueta_bi chamado={item.get('chamado_codigo')}: {e}"
                )
            
            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.info(f"Commit parcial etiqueta_bi: {i} registros processados")
        
        conn.commit()
    
    finally:
        cursor.close()
        conn.close()
    
    logger.info(
        f"chamados_etiqueta_bi | "
        f"INSERT={inseridos} "
        f"UPDATE={atualizados} "
        f"ERRO={erros}"
    )
    
    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "erros": erros,
    }