from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user
from gold.indicators.kpi_inadimplencia import calcular_kpi_inadimplencia

router = APIRouter()


def _empresas_autorizadas(usuario: dict) -> list[str] | None:
    """
    Retorna lista de codigo_empresa autorizados para o usuário.
    None = sem restrição (acessa todas).
    """
    empresas = usuario.get("empresas", [])
    if not empresas:
        return None
    return [e["codigo"] for e in empresas]


@router.get("/inadimplencia")
def get_inadimplencia(
    data_vencimento_inicial: Optional[str] = Query(None),
    data_vencimento_final:   Optional[str] = Query(None),
    empresas:                Optional[str] = Query(None, description="Códigos separados por vírgula"),
    status:                  Optional[str] = Query(None),
    limit:  int = Query(100, le=1000),
    offset: int = Query(1),
    usuario: dict = Depends(get_current_user),
):
    """
    Retorna inadimplência da view vw_bi_inadimplencia
    filtrada pelo tenant e pelas empresas autorizadas do usuário.

    O parâmetro `empresas` permite filtro multi-empresa no frontend:
    ex: empresas=1,3,7
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        # ── Filtro de tenant (obrigatório — isolamento total) ──
        filtros.append("tenant_id = %s")
        params.append(usuario["tenant_id"])

        # ── Filtro de empresas autorizadas ─────────────────────
        autorizadas = _empresas_autorizadas(usuario)

        # Empresas selecionadas pelo frontend
        empresas_frontend: list[str] = []
        if empresas:
            empresas_frontend = [e.strip() for e in empresas.split(",") if e.strip()]

        if autorizadas is not None:
            if empresas_frontend:
                permitidas = list(set(autorizadas) & set(empresas_frontend))
            else:
                permitidas = autorizadas

            if not permitidas:
                return {"total": 0, "data": []}

            placeholders = ", ".join(["%s"] * len(permitidas))
            filtros.append(f"codigo_empresa IN ({placeholders})")
            params.extend(permitidas)

        elif empresas_frontend:
            placeholders = ", ".join(["%s"] * len(empresas_frontend))
            filtros.append(f"codigo_empresa IN ({placeholders})")
            params.extend(empresas_frontend)

        # ── Filtros de data ────────────────────────────────────
        if data_vencimento_inicial:
            filtros.append("data_vencimento >= %s")
            params.append(data_vencimento_inicial)

        if data_vencimento_final:
            filtros.append("data_vencimento <= %s")
            params.append(data_vencimento_final)

        # ── Filtro de status ───────────────────────────────────
        if status:
            filtros.append("status_financeiro = %s")
            params.append(status)

        where = "WHERE " + " AND ".join(filtros) if filtros else ""

        # ── Paginação ──────────────────────────────────────────
        page_offset = (offset - 1) * limit

        cursor.execute(
            f"SELECT * FROM vw_bi_inadimplencia {where} "
            f"ORDER BY data_vencimento ASC "
            f"LIMIT %s OFFSET %s",
            (*params, limit, page_offset),
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
                elif hasattr(v, "__float__"):
                    try:
                        row[k] = float(v)
                    except Exception:
                        pass

        return {"total": len(rows), "data": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@router.get("/kpi/inadimplencia")
def kpi_inadimplencia(
    data_vencimento_inicial: Optional[str] = Query(None),
    data_vencimento_final:   Optional[str] = Query(None),
    empresas:                Optional[str] = Query(None),
    usuario: dict = Depends(get_current_user),
):
    """KPIs de inadimplência para o dashboard Angular."""
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = ["tenant_id = %s"]
        params  = [usuario["tenant_id"]]

        autorizadas = _empresas_autorizadas(usuario)
        empresas_frontend = [e.strip() for e in empresas.split(",")] if empresas else []

        if autorizadas is not None:
            permitidas = list(set(autorizadas) & set(empresas_frontend)) if empresas_frontend else autorizadas
            if not permitidas:
                return {"status": "ok", "data": {}}
            placeholders = ", ".join(["%s"] * len(permitidas))
            filtros.append(f"codigo_empresa IN ({placeholders})")
            params.extend(permitidas)
        elif empresas_frontend:
            placeholders = ", ".join(["%s"] * len(empresas_frontend))
            filtros.append(f"codigo_empresa IN ({placeholders})")
            params.extend(empresas_frontend)

        if data_vencimento_inicial:
            filtros.append("data_vencimento >= %s")
            params.append(data_vencimento_inicial)
        if data_vencimento_final:
            filtros.append("data_vencimento <= %s")
            params.append(data_vencimento_final)

        where = "WHERE " + " AND ".join(filtros)

        cursor.execute(f"""
            SELECT
                COUNT(*)                                               AS total_titulos,
                SUM(valor_total)                                       AS valor_total_inadimplente,
                COUNT(DISTINCT id_pessoa)                              AS total_clientes,
                SUM(CASE WHEN dias_atraso BETWEEN 1  AND 30  THEN valor_total ELSE 0 END) AS faixa_1_30,
                SUM(CASE WHEN dias_atraso BETWEEN 31 AND 60  THEN valor_total ELSE 0 END) AS faixa_31_60,
                SUM(CASE WHEN dias_atraso BETWEEN 61 AND 90  THEN valor_total ELSE 0 END) AS faixa_61_90,
                SUM(CASE WHEN dias_atraso > 90               THEN valor_total ELSE 0 END) AS faixa_acima_90
            FROM vw_bi_inadimplencia
            {where}
        """, params)

        resultado = cursor.fetchone() or {}
        for k, v in resultado.items():
            if v is not None:
                try:
                    resultado[k] = float(v)
                except Exception:
                    pass

        return {"status": "ok", "data": resultado}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
