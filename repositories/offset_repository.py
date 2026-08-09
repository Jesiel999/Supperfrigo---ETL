import logging
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


def ler_offset(tenant_id: int, origem: str, offset_inicial: int | None = None, valor_padrao: int = 1) -> int:
    """
    Retorna o offset de onde a extração deve começar.

    Prioridade:
      1. offset_inicial passado por parâmetro
      2. Offset salvo no banco 
    """
    if offset_inicial is not None:
        logger.info(f"[{origem}] tenant={tenant_id} | Offset forçado por parâmetro: {offset_inicial}")
        return offset_inicial

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT offset_atual FROM pipeline_offset WHERE tenant_id = %s AND origem = %s",
        (tenant_id, origem),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        logger.info(f"[{origem}] tenant={tenant_id} | Offset recuperado do banco: {row['offset_atual']}")
        return row["offset_atual"]

    logger.info(f"[{origem}] tenant={tenant_id} | Nenhum offset salvo. Iniciando do offset {valor_padrao}.")
    return valor_padrao


def salvar_offset(tenant_id: int, origem: str, offset: int) -> None:
    """Persiste (upsert) o offset atual no banco para essa origem/tenant."""
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pipeline_offset (tenant_id, origem, offset_atual)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE offset_atual = VALUES(offset_atual)
        """,
        (tenant_id, origem, offset),
    )
    conn.commit()
    cursor.close()
    conn.close()


def resetar_offset(tenant_id: int, origem: str, valor_padrao: int = 1) -> None:
    """
    Reseta o offset para valor_padrao após conclusão bem-sucedida (fim dos dados).
    Na próxima execução a varredura recomeça do início.
    """
    salvar_offset(tenant_id, origem, valor_padrao)
    logger.info(f"[{origem}] tenant={tenant_id} | Offset resetado para {valor_padrao}.")
