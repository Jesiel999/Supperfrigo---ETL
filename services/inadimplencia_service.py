from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger
import logging

logger = get_layer_logger("gold", "inadimplencia_service")


def listar_inadimplencia(
    id_empresa:      str | None = None,
    id_pessoa:       str | None = None,
    status:          str | None = None,
    dias_atraso_min: int | None = None,
    # limit:           int = 100,
    # offset:          int = 0,
) -> list[dict]:
    """Consulta a view vw_bi_inadimplencia com filtros dinâmicos."""
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        if id_empresa:
            filtros.append("id_empresa = %s")
            params.append(id_empresa)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if status:
            filtros.append("status_financeiro = %s")
            params.append(status)

        if dias_atraso_min is not None:
            filtros.append("dias_atraso >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_inadimplencia {where}",
            (params)
            # f"SELECT * FROM vw_bi_inadimplencia {where} LIMIT %s OFFSET %s",
            # (*params, limit, offset),
        )

        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return rows

    finally:
        cursor.close()
        conn.close()
