from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter()


# ── Helper: aplica a regra básica de acesso por empresa ─────────────
def _empresas_permitidas(current_user: dict) -> Optional[list]:
    """
    None  = usuário sem restrição no JWT (vê todas as empresas do empresa_bi)
    list  = lista de códigos (str) que o usuário PODE ver — qualquer coisa
            fora disso deve ser bloqueada, mesmo que o cliente peça.
    """
    empresas = current_user.get("empresas") or []
    if not empresas:
        return None
    return [str(e["codigo"]) for e in empresas]


def _aplicar_filtro_empresa(filtros: list, params: list, id_empresa: Optional[str], permitidas: Optional[list]):
    """
    Regra central: se o usuário tem restrição, SEMPRE filtra pelo que ele
    pode ver — ignora ou valida o id_empresa vindo da query string.
    Nunca confia no client para decidir o que ele pode ver.
    """
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


@router.get("/inadimplencia")
def get_inadimplencia(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    status:     Optional[str] = Query(None, description="VENCIDO | EM ABERTO"),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de inadimplência da view vw_bi_inadimplencia,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        if status:
            filtros.append("status_financeiro = %s")
            params.append(status)

        if dias_atraso_min is not None:
            filtros.append("dias_atraso >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_inadimplencia {where}",
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


@router.get("/pmp")
def get_pmp(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de prazo médio de pagamento da view vw_bi_pmp,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        if dias_atraso_min is not None:
            filtros.append("dias_pagamento >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_pmp {where}",
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


@router.get("/pmr")
def get_pmr(   # <-- renomeado (estava duplicado como get_pmp, sobrescrevia o nome)
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    dias_atraso_min: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna registros de prazo médio de recebimento da view vw_bi_pmr,
    restrito às empresas que o usuário logado pode ver.
    """
    conn   = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        filtros = []
        params  = []

        permitidas = _empresas_permitidas(current_user)
        _aplicar_filtro_empresa(filtros, params, id_empresa, permitidas)

        if id_pessoa:
            filtros.append("id_pessoa = %s")
            params.append(id_pessoa)

        if data_inicio:
            filtros.append("data_vencimento >= %s")
            params.append(data_inicio)

        if data_fim:
            filtros.append("data_vencimento <= %s")
            params.append(data_fim)

        if dias_atraso_min is not None:
            filtros.append("dias_recebimento >= %s")
            params.append(dias_atraso_min)

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        cursor.execute(
            f"SELECT * FROM vw_bi_pmr {where}",
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