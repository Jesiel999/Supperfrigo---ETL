from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

from api.routers.schemas.pessoa import (
    PessoaCreate,
    PessoaUpdate,
    PessoaOut,
    PessoaListaOut,
)


router = APIRouter(
    prefix="/api/pessoas",
    tags=["Colaboradores"],
    dependencies=[Depends(get_current_user)],
)


def _buscar_pessoa(cursor, pessoa_id: int):
    cursor.execute("""
        SELECT
            id,
            nome,
            cpf_cnpj,
            sexo,
            colaborador
        FROM pessoa_bi
        WHERE id = %s
        LIMIT 1
    """, (pessoa_id,))

    pessoa = cursor.fetchone()

    if not pessoa:
        raise HTTPException(
            status_code=404,
            detail="Colaborador não encontrado"
        )

    return pessoa


@router.get("", response_model=PessoaListaOut)
def listar_pessoas(
    busca: Optional[str] = None,
    colaborador: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    conn=Depends(connection_mysql),
):
    """
    Por padrão retorna só quem tem `colaborador = 1` (é essa a coluna
    que define quem aparece na tela de Colaboradores).
    """
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT id, nome, cpf_cnpj, sexo, colaborador
            FROM pessoa_bi
            WHERE 1 = 1
        """
        params = []

        if colaborador is not None:
            sql += " AND colaborador = %s"
            params.append(1 if colaborador else 0)

        if busca:
            sql += " AND (nome LIKE %s OR cpf_cnpj LIKE %s)"
            termo = f"%{busca}%"
            params.extend([termo, termo])

        cursor.execute(
            f"SELECT COUNT(*) AS total FROM ({sql}) AS sub",
            params
        )
        total = cursor.fetchone()["total"]

        sql += " ORDER BY nome LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cursor.execute(sql, params)
        itens = cursor.fetchall()

        return PessoaListaOut(total=total, itens=itens)

    finally:
        cursor.close()
        conn.close()


@router.get("/{pessoa_id}", response_model=PessoaOut)
def obter_pessoa(
    pessoa_id: int,
    conn=Depends(connection_mysql),
):
    cursor = conn.cursor(dictionary=True)

    try:
        return _buscar_pessoa(cursor, pessoa_id)

    finally:
        cursor.close()
        conn.close()


@router.post("", response_model=PessoaOut, status_code=201)
def criar_pessoa(
    payload: PessoaCreate,
    conn=Depends(connection_mysql),
):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO pessoa_bi (nome, cpf_cnpj, sexo, colaborador)
            VALUES (%s, %s, %s, %s)
        """, (
            payload.nome,
            payload.cpf_cnpj,
            payload.sexo,
            payload.colaborador,
        ))

        pessoa_id = cursor.lastrowid

        conn.commit()

        return _buscar_pessoa(cursor, pessoa_id)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.put("/{pessoa_id}", response_model=PessoaOut)
def atualizar_pessoa(
    pessoa_id: int,
    payload: PessoaUpdate,
    conn=Depends(connection_mysql),
):
    cursor = conn.cursor(dictionary=True)

    try:
        _buscar_pessoa(cursor, pessoa_id)

        dados = payload.model_dump(exclude_unset=True)

        if not dados:
            return _buscar_pessoa(cursor, pessoa_id)

        set_clause = ", ".join(f"{campo} = %s" for campo in dados)
        valores = list(dados.values())
        valores.append(pessoa_id)

        cursor.execute(
            f"UPDATE pessoa_bi SET {set_clause} WHERE id = %s",
            valores
        )

        conn.commit()

        return _buscar_pessoa(cursor, pessoa_id)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.delete("/{pessoa_id}", status_code=204)
def excluir_pessoa(
    pessoa_id: int,
    conn=Depends(connection_mysql),
):
    """
    Soft delete: só desmarca `colaborador`, nunca apaga a linha de
    pessoa_bi — ela pode estar referenciada em equipamento_movimentacao,
    parque_tecnologico.id_colaborador e chip.id_colaborador.
    """
    cursor = conn.cursor(dictionary=True)

    try:
        _buscar_pessoa(cursor, pessoa_id)

        cursor.execute("""
            UPDATE pessoa_bi
            SET colaborador = 0
            WHERE id = %s
        """, (pessoa_id,))

        conn.commit()

        return None

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
