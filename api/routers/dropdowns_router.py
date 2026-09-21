from typing import Optional

from fastapi import APIRouter, Depends, Query

from database.mysql_connection import connection_mysql
from api.routers.schemas.dropdown import DropdownItem
from auth.router import get_current_user

router = APIRouter(prefix="/api", tags=["Dropdowns"])


@router.get("/tipos-equipamento", response_model=list[DropdownItem])
def listar_tipos_equipamento(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),
):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nome
            FROM tipo_equipamento
            ORDER BY nome
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/marcas", response_model=list[DropdownItem])
def listar_marcas(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nome
            FROM marca
            ORDER BY nome
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/modelos", response_model=list[DropdownItem])
def listar_modelos(
    id_marca: Optional[int] = Query(None),
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),
):
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT
                id,
                nome
            FROM modelo
        """

        params = []

        if id_marca is not None:
            sql += """
                WHERE id_marca = %s
            """
            params.append(id_marca)

        sql += """
            ORDER BY nome
        """

        cursor.execute(sql, params)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/toners", response_model=list[DropdownItem])
def listar_toners(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nome
            FROM toner
            ORDER BY nome
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/departamentos", response_model=list[DropdownItem])
def listar_departamentos(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                nome
            FROM dim_departamento
            ORDER BY nome
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/empresas", response_model=list[DropdownItem])
def listar_empresas(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                codigo_empresa,
                nome_empresa
            FROM empresa_bi
            ORDER BY nome_empresa
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["codigo_empresa"],
                nome=row["nome_empresa"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


@router.get("/monitores-disponiveis", response_model=list[DropdownItem])
def listar_monitores_disponiveis(conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user),):
    """
    Lista monitores ativos que ainda não estão vinculados
    como id_monitor de outro equipamento.
    """

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                e.id,
                e.nome
            FROM parque_tecnologico e
            INNER JOIN tipo_equipamento t
                ON t.id = e.id_tipo
            WHERE LOWER(t.nome) LIKE '%monitor%'
              AND e.ativo = 1
            ORDER BY e.nome
        """)

        rows = cursor.fetchall()

        return [
            DropdownItem(
                id=row["id"],
                nome=row["nome"]
            )
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()