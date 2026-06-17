import logging
from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("gold", "kpi_inadimplencia")


def calcular_kpi_inadimplencia() -> dict:
    """
    Calcula KPIs de inadimplência diretamente da view vw_bi_inadimplencia.
    Retorna dict com totais por faixa de atraso e valor total inadimplente.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                COUNT(*)                                        AS total_titulos,
                SUM(valor_total)                               AS valor_total_inadimplente,
                SUM(CASE WHEN dias_atraso BETWEEN 1  AND 30   THEN valor_total ELSE 0 END) AS faixa_1_30,
                SUM(CASE WHEN dias_atraso BETWEEN 31 AND 60   THEN valor_total ELSE 0 END) AS faixa_31_60,
                SUM(CASE WHEN dias_atraso BETWEEN 61 AND 90   THEN valor_total ELSE 0 END) AS faixa_61_90,
                SUM(CASE WHEN dias_atraso > 90                 THEN valor_total ELSE 0 END) AS faixa_acima_90,
                COUNT(DISTINCT id_pessoa)                      AS total_clientes_inadimplentes,
                COUNT(DISTINCT id_empresa)                     AS total_empresas
            FROM vw_bi_inadimplencia
        """)
        resultado = cursor.fetchone()

        logger.info(f"KPI Inadimplência calculado: {resultado}")
        return resultado or {}

    except Exception as e:
        logger.error(f"Erro ao calcular KPI inadimplência: {e}")
        return {}

    finally:
        cursor.close()
        conn.close()
