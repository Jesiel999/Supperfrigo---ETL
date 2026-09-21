from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from mysql.connector.errors import IntegrityError

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

from api.routers.schemas.dropdown import DropdownItem, NomeSimplesPayload

router = APIRouter()

def criar_router_cadastro_simples(
    tabela: str,
    prefix: str,
    tag: str,
    nome_singular: str,
    current_user: dict = Depends(get_current_user),
) -> APIRouter:

    router = APIRouter(prefix=prefix, tags=[tag])

    def _buscar(cursor, item_id: int):
        cursor.execute(
            f"SELECT id, nome FROM {tabela} WHERE id = %s LIMIT 1",
            (item_id,)
        )

        item = cursor.fetchone()

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"{nome_singular} não encontrado(a)"
            )

        return item

    @router.get("", response_model=list[DropdownItem])
    def listar(
        busca: Optional[str] = Query(None),
        conn=Depends(connection_mysql),
        current_user: dict = Depends(get_current_user),
    ):
        cursor = conn.cursor(dictionary=True)

        try:
            sql = f"SELECT id, nome FROM {tabela} WHERE 1 = 1"
            params = []

            if busca:
                sql += " AND nome LIKE %s"
                params.append(f"%{busca}%")

            sql += " ORDER BY nome"

            cursor.execute(sql, params)

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

    @router.get("/{item_id}", response_model=DropdownItem)
    def obter(
        item_id: int,
        conn=Depends(connection_mysql),
        current_user: dict = Depends(get_current_user),
    ):
        cursor = conn.cursor(dictionary=True)

        try:
            return _buscar(cursor, item_id)

        finally:
            cursor.close()
            conn.close()

    @router.post("", response_model=DropdownItem, status_code=201)
    def criar(
        payload: NomeSimplesPayload,
        conn=Depends(connection_mysql),
        current_user: dict = Depends(get_current_user),
    ):
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                f"INSERT INTO {tabela} (nome) VALUES (%s)",
                (payload.nome,)
            )

            novo_id = cursor.lastrowid

            conn.commit()

            return _buscar(cursor, novo_id)

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    @router.put("/{item_id}", response_model=DropdownItem)
    def atualizar(
        item_id: int,
        payload: NomeSimplesPayload,
        conn=Depends(connection_mysql),
        current_user: dict = Depends(get_current_user),
    ):
        cursor = conn.cursor(dictionary=True)

        try:
            _buscar(cursor, item_id)

            cursor.execute(
                f"UPDATE {tabela} SET nome = %s WHERE id = %s",
                (payload.nome, item_id)
            )

            conn.commit()

            return _buscar(cursor, item_id)

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    @router.delete("/{item_id}", status_code=204)
    def excluir(
        item_id: int,
        conn=Depends(connection_mysql),
        current_user: dict = Depends(get_current_user),
    ):
        cursor = conn.cursor(dictionary=True)

        try:
            _buscar(cursor, item_id)

            cursor.execute(
                f"DELETE FROM {tabela} WHERE id = %s",
                (item_id,)
            )

            conn.commit()

            return None

        except IntegrityError:
            conn.rollback()
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Não é possível excluir: existem equipamentos vinculados "
                    f"a esta(e) {nome_singular.lower()}."
                ),
            )

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    return router
