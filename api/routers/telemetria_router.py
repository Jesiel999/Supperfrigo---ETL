from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter()


# ── Helper: aplica a regra básica de acesso por empresa ─────────────
def _empresas_permitidas(
    current_user: dict
) -> Optional[list]:

    empresas = current_user.get("empresas") or []

    if not empresas:
        return None

    return [str(e["codigo"]) for e in empresas]


def _aplicar_filtro_empresa(
    filtros: list, 
    params: list, 
    id_empresa: Optional[str], 
    permitidas: Optional[list]
):

    if permitidas is not None:
        if id_empresa:
            if id_empresa not in permitidas:
                raise HTTPException(status_code=403, detail="Sem acesso a esta empresa")
            
            filtros.append("id_empresa = %s")
            params.append(id_empresa)

        else:
            placeholders = ",".join(["%s"] * len(permitidas))
            filtros.append(f"id_empresa IN ({placeholders})")
            params.extend(permitidas)

    elif id_empresa:
        filtros.append("id_empresa = %s")
        params.append(id_empresa)


@router.get("/frota")
def get_inadimplencia(
    id_empresa: Optional[str] = Query(None),
    dispositivo_id:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):

    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if dispositivo_id:
            filtros.append("dispositivo_id = %s")
            params.append(dispositivo_id)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_telemetria_frota {where}",
            params,
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

