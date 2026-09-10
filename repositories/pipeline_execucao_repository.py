from datetime import datetime
from typing import Any

from database.mysql_connection import connection_mysql


def iniciar_execucao(
    pipeline_offset_id: int,
    tenant_id: int,
    offset_inicial: int | None = None,
) -> int:
    """
    Cria o registro histórico de uma execução.

    A execução começa com status EXECUTANDO e será
    finalizada pela Pipeline ao término.
    """

    conn = connection_mysql()

    try:
        cursor = conn.cursor()

        sql = """
            INSERT INTO pipeline_execucao (
                pipeline_offset_id,
                tenant_id,
                inicio_execucao,
                status,
                offset_inicial
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        cursor.execute(
            sql,
            (
                pipeline_offset_id,
                tenant_id,
                datetime.now(),
                "EXECUTANDO",
                offset_inicial,
            ),
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def finalizar_execucao(
    execucao_id: int,
    metrics: Any,
    status: str,
    offset_final: int | None = None,
    mensagem_erro: str | None = None,
) -> None:
    """
    Finaliza uma execução e grava suas métricas.
    """

    conn = connection_mysql()

    try:
        cursor = conn.cursor()

        sql = """
            UPDATE pipeline_execucao
            SET
                fim_execucao = %s,
                status = %s,

                tempo_total_segundos = %s,
                velocidade_reg_por_segundo = %s,

                total_processados = %s,
                total_inseridos = %s,
                total_atualizados = %s,
                total_ignorados = %s,
                total_erros = %s,

                offset_final = %s,
                mensagem_erro = %s

            WHERE id = %s
        """

        cursor.execute(
            sql,
            (
                datetime.now(),
                status,

                metrics.elapsed,
                metrics.velocidade,

                metrics.total_processados,
                metrics.total_inseridos,
                metrics.total_atualizados,
                metrics.total_ignorados,
                metrics.total_erros,

                offset_final,
                mensagem_erro,

                execucao_id,
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
