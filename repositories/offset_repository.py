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
        # logger.info(f"[{origem}] tenant={tenant_id} | Offset forçado por parâmetro: {offset_inicial}")
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
        # logger.info(f"[{origem}] tenant={tenant_id} | Offset recuperado do banco: {row['offset_atual']}")
        return row["offset_atual"]

    # logger.info(f"[{origem}] tenant={tenant_id} | Nenhum offset salvo. Iniciando do offset {valor_padrao}.")
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
    # logger.info(f"[{origem}] tenant={tenant_id} | Offset resetado para {valor_padrao}.")

def marcar_inicio_execucao(tenant_id: int, origem: str, endpoint: str) -> None:
    """Chamar no início de cada execução da pipeline, antes de qualquer request."""
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pipeline_offset (tenant_id, origem, endpoint, status, ultima_execucao)
        VALUES (%s, %s, %s, 'EM_EXECUCAO', NOW())
        ON DUPLICATE KEY UPDATE
            endpoint = VALUES(endpoint),
            status = 'EM_EXECUCAO',
            ultima_execucao = NOW()
        """,
        (tenant_id, origem, endpoint),
    )
    conn.commit()
    cursor.close()
    conn.close()

def registrar_pagina_processada(tenant_id: int, origem: str, offset: int, qtd_registros: int) -> None:
    """
    Chamar SOMENTE depois que a página já foi persistida com sucesso na Bronze.
    Avança offset_atual, soma registros_processados e marca ultimo_sucesso —
    tudo num único UPDATE (mesmo "commit" lógico do avanço de offset).
    """
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE pipeline_offset
        SET offset_atual = %s,
            registros_processados = registros_processados + %s,
            status = 'EM_EXECUCAO',
            ultimo_sucesso = NOW()
        WHERE tenant_id = %s AND origem = %s
        """,
        (offset, qtd_registros, tenant_id, origem),
    )
    conn.commit()
    cursor.close()
    conn.close()


def marcar_concluido(tenant_id: int, origem: str, valor_padrao_offset: int = 1) -> None:
    """Fim da paginação (página vazia) — reseta offset e marca status CONCLUIDO."""
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE pipeline_offset
        SET offset_atual = %s,
            status = 'CONCLUIDO',
            ultimo_sucesso = NOW()
        WHERE tenant_id = %s AND origem = %s
        """,
        (valor_padrao_offset, tenant_id, origem),
    )
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"[{origem}] tenant={tenant_id} | status=CONCLUIDO, offset resetado para {valor_padrao_offset}.")
    # logger.info(f"[{origem}] tenant={tenant_id} | status=CONCLUIDO, offset resetado para {valor_padrao_offset}.")


def marcar_erro(tenant_id: int, origem: str, erro: str) -> None:
    """
    Registra falha SEM alterar offset_atual — é isso que garante que a
    próxima execução retoma exatamente do mesmo lugar.
    """
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE pipeline_offset
        SET status = 'ERRO',
            ultimo_erro = %s
        WHERE tenant_id = %s AND origem = %s
        """,
        (erro[:5000], tenant_id, origem),
    )
    conn.commit()
    cursor.close()
    conn.close()
    logger.error(f"[{origem}] tenant={tenant_id} | status=ERRO | offset NÃO avançado | {erro}")
    # logger.error(f"[{origem}] tenant={tenant_id} | status=ERRO | offset NÃO avançado | {erro}")
