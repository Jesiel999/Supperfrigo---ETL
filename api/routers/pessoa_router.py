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


def _buscar_pessoa_por_cpf(cursor, cpf_cnpj: str):
    cursor.execute("""
        SELECT
            id,
            nome,
            cpf_cnpj,
            sexo,
            colaborador
        FROM pessoa_bi
        WHERE cpf_cnpj = %s
        LIMIT 1
    """, (cpf_cnpj,))

    return cursor.fetchone()


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
    """
    Antes de inserir, verifica se já existe uma pessoa com esse
    cpf_cnpj (a coluna é UNIQUE em pessoa_bi, então um INSERT direto
    estouraria erro de integridade em vez de uma mensagem clara):

    - CPF já existe E já é colaborador  -> 409, não duplica.
    - CPF já existe mas não é colaborador (ex.: já era cliente/fornecedor
      na base) -> reaproveita a linha, só marca colaborador = 1 e
      atualiza nome/sexo se vierem preenchidos. Não cria uma pessoa nova.
    - CPF não existe (ou não foi informado) -> cria normalmente.
    """
    cursor = conn.cursor(dictionary=True)

    try:
        pessoa_existente = None

        if payload.cpf_cnpj:
            pessoa_existente = _buscar_pessoa_por_cpf(cursor, payload.cpf_cnpj)

        if pessoa_existente:
            if pessoa_existente["colaborador"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Já existe um colaborador cadastrado com o CPF/CNPJ {payload.cpf_cnpj}."
                )

            # Pessoa já existia na base (ex.: cliente) mas ainda não era
            # colaborador — reaproveita a linha em vez de duplicar.
            cursor.execute("""
                UPDATE pessoa_bi
                SET
                    nome = %s,
                    sexo = %s,
                    colaborador = 1
                WHERE id = %s
            """, (
                payload.nome or pessoa_existente["nome"],
                payload.sexo if payload.sexo is not None else pessoa_existente["sexo"],
                pessoa_existente["id"],
            ))

            conn.commit()

            return _buscar_pessoa(cursor, pessoa_existente["id"])

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

    except HTTPException:
        raise

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.post("/{cpf_cnpj}/colaborador", response_model=PessoaOut)
def tornar_colaborador(
    cpf_cnpj: str,
    conn=Depends(connection_mysql),
):
    """
    Marca como colaborador uma pessoa que já existe em pessoa_bi
    (ex.: sincronizada de outro sistema como cliente/fornecedor),
    identificada pelo CPF/CNPJ. Não cria pessoa nova — se o CPF não
    existir na base, retorna 404.
    """
    cursor = conn.cursor(dictionary=True)

    try:
        pessoa = _buscar_pessoa_por_cpf(cursor, cpf_cnpj)

        if not pessoa:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma pessoa encontrada com o CPF/CNPJ {cpf_cnpj}."
            )

        if pessoa["colaborador"]:
            raise HTTPException(
                status_code=409,
                detail=f"Essa pessoa (CPF/CNPJ {cpf_cnpj}) já é colaborador."
            )

        cursor.execute("""
            UPDATE pessoa_bi
            SET colaborador = 1
            WHERE id = %s
        """, (pessoa["id"],))

        conn.commit()

        return _buscar_pessoa(cursor, pessoa["id"])

    except HTTPException:
        raise

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

        # Se o CPF está sendo alterado, garante que não colide com outra pessoa.
        if dados.get("cpf_cnpj"):
            conflito = _buscar_pessoa_por_cpf(cursor, dados["cpf_cnpj"])
            if conflito and conflito["id"] != pessoa_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Já existe outra pessoa cadastrada com o CPF/CNPJ {dados['cpf_cnpj']}."
                )

        set_clause = ", ".join(f"{campo} = %s" for campo in dados)
        valores = list(dados.values())
        valores.append(pessoa_id)

        cursor.execute(
            f"UPDATE pessoa_bi SET {set_clause} WHERE id = %s",
            valores
        )

        conn.commit()

        return _buscar_pessoa(cursor, pessoa_id)

    except HTTPException:
        raise

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