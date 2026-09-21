from datetime import datetime
from typing import Optional
from auth.router import get_current_user

from fastapi import APIRouter, Depends, HTTPException, Query

from database.mysql_connection import connection_mysql

from api.routers.schemas.chip import (
    ChipCreate,
    ChipUpdate,
    ChipOut,
)

from api.routers.schemas.equipamento import (
    MovimentacaoOut,
    VincularRequest,
    DevolverRequest,
)


router = APIRouter(
    prefix="/api/chips",
    tags=["Chips"]
)


def _buscar_chip(
    cursor, chip_id: int,
    current_user: dict = Depends(get_current_user)
):
    cursor.execute("""
        SELECT
            c.id,
            c.id_empresa,
            c.id_departamento,
            c.id_colaborador,
            c.numero,
            c.iccid,

            p.nome AS nome_colaborador,
            emp.nome_empresa AS nome_empresa

        FROM chips c

        LEFT JOIN pessoa_bi p
            ON p.id = c.id_colaborador

        LEFT JOIN empresa_bi emp
            ON emp.codigo_empresa = c.id_empresa

        WHERE c.id = %s

        LIMIT 1
    """, (chip_id,))

    chip = cursor.fetchone()

    if not chip:
        raise HTTPException(
            status_code=404,
            detail="Chip não encontrado"
        )

    return chip


def _to_out(chip) -> ChipOut:
    return ChipOut(
        id=chip["id"],
        id_empresa=chip["id_empresa"],
        id_departamento=chip["id_departamento"],
        id_colaborador=chip["id_colaborador"],
        numero=chip["numero"],
        iccid=chip["iccid"],
        nome_colaborador=chip["nome_colaborador"],
        nome_empresa=chip["nome_empresa"],
    )


@router.get("", response_model=list[ChipOut])
def listar_chips(
    empresa: Optional[int] = None,
    colaborador: Optional[int] = None,
    busca: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT
                c.id,
                c.id_empresa,
                c.id_departamento,
                c.id_colaborador,
                c.numero,
                c.iccid,

                p.nome AS nome_colaborador,
                emp.nome_empresa AS nome_empresa

            FROM chips c

            LEFT JOIN pessoa_bi p
                ON p.id = c.id_colaborador

            LEFT JOIN empresa_bi emp
                ON emp.codigo_empresa = c.id_empresa

            WHERE 1 = 1
        """

        params = []

        if empresa is not None:
            sql += """
                AND c.id_empresa = %s
            """
            params.append(empresa)

        if colaborador is not None:
            sql += """
                AND c.id_colaborador = %s
            """
            params.append(colaborador)

        if busca:
            sql += """
                AND (
                    c.numero LIKE %s
                    OR c.iccid LIKE %s
                )
            """

            termo = f"%{busca}%"
            params.extend([termo, termo])

        sql += """
            ORDER BY c.numero
            LIMIT %s OFFSET %s
        """

        params.extend([limit, skip])

        cursor.execute(sql, params)

        chips = cursor.fetchall()

        return [_to_out(chip) for chip in chips]

    finally:
        cursor.close()
        conn.close()


@router.post(
    "",
    response_model=ChipOut,
    status_code=201
)
def criar_chip(
    payload: ChipCreate,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        dados = payload.model_dump(exclude_unset=True)

        if not dados:
            raise HTTPException(
                status_code=400,
                detail="Nenhum dado informado"
            )

        campos_permitidos = {
            "id_empresa",
            "id_departamento",
            "numero",
            "iccid",
        }

        dados = {
            campo: valor
            for campo, valor in dados.items()
            if campo in campos_permitidos
        }

        campos = list(dados.keys())
        valores = list(dados.values())

        placeholders = ", ".join(["%s"] * len(campos))
        nomes_campos = ", ".join(campos)

        sql = f"""
            INSERT INTO chips ({nomes_campos})
            VALUES ({placeholders})
        """

        cursor.execute(sql, valores)

        chip_id = cursor.lastrowid

        # ---------------------------------------------------------
        # Cria movimentação caso já venha vinculado
        # ---------------------------------------------------------
        if dados.get("id_colaborador"):
            cursor.execute("""
                INSERT INTO equipamento_movimentacao (
                    tipo_ativo,
                    id_ativo,
                    id_colaborador,
                    data_vinculo
                )
                VALUES (
                    'chip',
                    %s,
                    %s,
                    %s
                )
            """, (
                chip_id,
                dados["id_colaborador"],
                datetime.now(),
            ))

        conn.commit()

        chip = _buscar_chip(cursor, chip_id)

        return _to_out(chip)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.put(
    "/{chip_id}",
    response_model=ChipOut
)
def atualizar_chip(
    chip_id: int,
    payload: ChipUpdate,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        _buscar_chip(cursor, chip_id)

        dados = payload.model_dump(exclude_unset=True)

        campos_permitidos = {
            "id_empresa",
            "id_departamento",
            "id_colaborador",
            "numero",
            "iccid",
        }

        dados = {
            campo: valor
            for campo, valor in dados.items()
            if campo in campos_permitidos
        }

        if not dados:
            return _to_out(_buscar_chip(cursor, chip_id))

        set_clause = ", ".join(
            f"{campo} = %s"
            for campo in dados
        )

        valores = list(dados.values())
        valores.append(chip_id)

        sql = f"""
            UPDATE chips
            SET {set_clause}
            WHERE id = %s
        """

        cursor.execute(sql, valores)

        conn.commit()

        return _to_out(_buscar_chip(cursor, chip_id))

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.delete(
    "/{chip_id}",
    status_code=204
)
def excluir_chip(
    chip_id: int,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        _buscar_chip(cursor, chip_id)

        cursor.execute("""
            DELETE FROM chips
            WHERE id = %s
        """, (chip_id,))

        conn.commit()

        return None

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.post(
    "/{chip_id}/vincular",
    response_model=ChipOut
)
def vincular_chip(
    chip_id: int,
    payload: VincularRequest,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        chip = _buscar_chip(cursor, chip_id)

        # ---------------------------------------------------------
        # Verifica colaborador
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                nome
            FROM pessoa_bi
            WHERE id = %s
            LIMIT 1
        """, (payload.id_colaborador,))

        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(
                status_code=404,
                detail="Colaborador não encontrado"
            )

        # ---------------------------------------------------------
        # Verifica vínculo atual
        # ---------------------------------------------------------
        if chip["id_colaborador"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Chip já está vinculado a outro colaborador. "
                    "Devolva antes de vincular."
                )
            )

        # ---------------------------------------------------------
        # Vincula chip
        # ---------------------------------------------------------
        cursor.execute("""
            UPDATE chips
            SET id_colaborador = %s
            WHERE id = %s
        """, (
            payload.id_colaborador,
            chip_id,
        ))

        # ---------------------------------------------------------
        # Registra movimentação
        # ---------------------------------------------------------
        cursor.execute("""
            INSERT INTO equipamento_movimentacao (
                tipo_ativo,
                id_ativo,
                id_colaborador,
                data_vinculo,
                observacao
            )
            VALUES (
                'chip',
                %s,
                %s,
                %s,
                %s
            )
        """, (
            chip_id,
            payload.id_colaborador,
            datetime.now(),
            payload.observacao,
        ))

        conn.commit()

        return _to_out(_buscar_chip(cursor, chip_id))

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.post(
    "/{chip_id}/devolver",
    response_model=ChipOut
)
def devolver_chip(
    chip_id: int,
    payload: DevolverRequest,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        chip = _buscar_chip(cursor, chip_id)

        if not chip["id_colaborador"]:
            raise HTTPException(
                status_code=400,
                detail="Chip não está vinculado a ninguém"
            )

        # ---------------------------------------------------------
        # Busca movimentação aberta
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                id_colaborador,
                data_vinculo,
                data_devolucao,
                observacao
            FROM equipamento_movimentacao

            WHERE tipo_ativo = 'chip'
              AND id_ativo = %s
              AND id_colaborador = %s
              AND data_devolucao IS NULL

            ORDER BY data_vinculo DESC

            LIMIT 1
        """, (
            chip_id,
            chip["id_colaborador"],
        ))

        movimentacao = cursor.fetchone()

        # ---------------------------------------------------------
        # Fecha movimentação
        # ---------------------------------------------------------
        if movimentacao:
            observacao = (
                payload.observacao
                if payload.observacao
                else movimentacao["observacao"]
            )

            cursor.execute("""
                UPDATE equipamento_movimentacao
                SET
                    data_devolucao = %s,
                    observacao = %s
                WHERE id = %s
            """, (
                datetime.now(),
                observacao,
                movimentacao["id"],
            ))

        # ---------------------------------------------------------
        # Remove colaborador do chip
        # ---------------------------------------------------------
        cursor.execute("""
            UPDATE chips
            SET id_colaborador = NULL
            WHERE id = %s
        """, (chip_id,))

        conn.commit()

        return _to_out(_buscar_chip(cursor, chip_id))

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


@router.get(
    "/{chip_id}/historico",
    response_model=list[MovimentacaoOut]
)
def historico_chip(
    chip_id: int,
    conn=Depends(connection_mysql),
    current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor(dictionary=True)

    try:
        _buscar_chip(cursor, chip_id)

        # ---------------------------------------------------------
        # Histórico
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                m.id,
                m.id_colaborador,
                p.nome AS nome_colaborador,
                m.data_vinculo,
                m.data_devolucao,
                m.observacao

            FROM equipamento_movimentacao m

            LEFT JOIN pessoa_bi p
                ON p.id = m.id_colaborador

            WHERE m.tipo_ativo = 'chip'
              AND m.id_ativo = %s

            ORDER BY m.data_vinculo DESC
        """, (chip_id,))

        movimentacoes = cursor.fetchall()

        return [
            MovimentacaoOut(
                id=m["id"],
                id_colaborador=m["id_colaborador"],
                nome_colaborador=m["nome_colaborador"],
                data_vinculo=m["data_vinculo"],
                data_devolucao=m["data_devolucao"],
                observacao=m["observacao"],
            )
            for m in movimentacoes
        ]

    finally:
        cursor.close()
        conn.close()