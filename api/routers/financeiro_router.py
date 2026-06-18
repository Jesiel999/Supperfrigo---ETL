from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from database.mysql_connection import connection_mysql
from auth.router import get_current_user

router = APIRouter()


@router.get("/inadimplencia")
def get_inadimplencia(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    status:     Optional[str] = Query(None, description="VENCIDO | EM_ABERTO"),
    dias_atraso_min: Optional[int] = Query(None),
    # limit:      int = Query(100, le=1000),
    # offset:     int = Query(0),
    _user: str = Depends(get_current_user),
):
    """
    Retorna registros de inadimplência da view vw_bi_inadimplencia.
    """
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
            (params)
            # f"SELECT * FROM vw_bi_inadimplencia {where} LIMIT %s OFFSET %s",
            # (*params, limit, offset),
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

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
    # limit:      int = Query(100, le=1000),
    # offset:     int = Query(0),
    _user: str = Depends(get_current_user),
):
    """
    Retorna registros de prazo medio pagamento da view vw_bi_pmp.
    """
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
            (params)
            # f"SELECT * FROM vw_bi_pmp {where} LIMIT %s OFFSET %s",
            # (*params, limit, offset),
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@router.get("/pmr")
def get_pmp(
    id_empresa: Optional[str] = Query(None),
    id_pessoa:  Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim:  Optional[str] = Query(None),
    dias_atraso_min: Optional[int] = Query(None),
    # limit:      int = Query(100, le=1000),
    # offset:     int = Query(0),
    _user: str = Depends(get_current_user),
):
    """
    Retorna registros de prazo medio pagamento da view vw_bi_pmr.
    """
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
            (params)
            # f"SELECT * FROM vw_bi_pmr {where} LIMIT %s OFFSET %s",
            # (*params, limit, offset),
        )
        rows = cursor.fetchall()

        for row in rows:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()

        return {"total": len(rows), "data": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


