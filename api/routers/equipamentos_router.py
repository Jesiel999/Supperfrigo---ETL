from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from database.mysql_connection import connection_mysql
from auth.router import get_current_user

from api.routers.schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoUpdate,
    EquipamentoOut,
    EquipamentoListaOut,
    MovimentacaoOut,
    VincularRequest,
    DevolverRequest,
    ResumoEquipamentos,
)

router = APIRouter(
    prefix="/api/equipamentos",
    tags=["Equipamentos"],
    dependencies=[Depends(get_current_user)],
)

# ============================================================

# HELPERS

# ============================================================

def _get_equipamento_or_404(cursor, equipamento_id: int):

    sql = """
        SELECT
            e.id,
            e.nome,
            e.id_empresa,
            e.id_tipo,
            e.id_departamento,
            e.id_marca,
            e.id_modelo,
            e.id_toner,
            e.id_monitor,
            e.id_colaborador,
            e.senha,
            e.scanner,
            e.data_fabricacao,
            e.serie,
            e.processador,
            e.memoria_ram,
            e.armazenamento,
            e.tamanho,
            e.so,
            e.ip,
            e.mac,
            e.observacao,
            e.ativo,

            emp.nome_empresa AS nome_empresa,
            tipo.nome AS nome_tipo,
            marca.nome AS nome_marca,
            modelo.nome AS nome_modelo,
            pessoa.nome AS nome_colaborador

        FROM parque_tecnologico e

        LEFT JOIN empresa_bi emp
            ON emp.codigo_empresa = e.id_empresa

        LEFT JOIN tipo_equipamento tipo
            ON tipo.id = e.id_tipo

        LEFT JOIN marca
            ON marca.id = e.id_marca

        LEFT JOIN modelo
            ON modelo.id = e.id_modelo

        LEFT JOIN pessoa_bi pessoa
            ON pessoa.id = e.id_colaborador

        WHERE e.id = %s

        LIMIT 1
    """

    cursor.execute(sql, (equipamento_id,))
    equipamento = cursor.fetchone()

    if not equipamento:
        raise HTTPException(
            status_code=404,
            detail="Equipamento não encontrado",
        )

    # IMPORTANTE:
    # O return precisa ficar FORA do if.
    return equipamento


def _normalizar_equipamento(row: dict) -> dict:
    """
    Normaliza o retorno do MySQL para o schema EquipamentoOut.
    """


    return {
        "id": row.get("id"),
        "nome": row.get("nome"),
        "id_empresa": row.get("id_empresa"),
        "id_tipo": row.get("id_tipo"),
        "id_departamento": row.get("id_departamento"),
        "id_marca": row.get("id_marca"),
        "id_modelo": row.get("id_modelo"),
        "id_toner": row.get("id_toner"),
        "id_monitor": row.get("id_monitor"),
        "id_colaborador": row.get("id_colaborador"),
        "senha": row.get("senha"),
        "scanner": row.get("scanner"),
        "data_fabricacao": row.get("data_fabricacao"),
        "serie": row.get("serie"),
        "processador": row.get("processador"),
        "memoria_ram": row.get("memoria_ram"),
        "armazenamento": row.get("armazenamento"),
        "tamanho": row.get("tamanho"),
        "so": row.get("so"),
        "ip": row.get("ip"),
        "mac": row.get("mac"),
        "observacao": row.get("observacao"),
        "ativo": row.get("ativo"),
        "nome_empresa": row.get("nome_empresa"),
        "nome_tipo": row.get("nome_tipo"),
        "nome_marca": row.get("nome_marca"),
        "nome_modelo": row.get("nome_modelo"),
        "nome_colaborador": row.get("nome_colaborador"),
    }


def _fechar(conn, cursor):
    """
    Fecha cursor e conexão com segurança.
    """


    try:
        cursor.close()
    except Exception:
        pass

    try:
        conn.close()
    except Exception:
        pass


# ============================================================

# LISTAR

# ============================================================

@router.get("",response_model=EquipamentoListaOut,)
def listar_equipamentos(
tipo: Optional[int] = None,
empresa: Optional[int] = None,
departamento: Optional[int] = None,
colaborador: Optional[int] = None,
busca: Optional[str] = None,
ativo: Optional[bool] = True,
skip: int = Query(0, ge=0),
limit: int = Query(50, ge=1, le=200),
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        where = []
        params = []

        # ----------------------------------------------------
        # FILTROS
        # ----------------------------------------------------

        if ativo is not None:
            where.append("e.ativo = %s")
            params.append(1 if ativo else 0)

        if tipo is not None:
            where.append("e.id_tipo = %s")
            params.append(tipo)

        if empresa is not None:
            where.append("e.id_empresa = %s")
            params.append(empresa)

        if departamento is not None:
            where.append("e.id_departamento = %s")
            params.append(departamento)

        if colaborador is not None:
            where.append("e.id_colaborador = %s")
            params.append(colaborador)

        if busca:
            termo = f"%{busca}%"

            where.append(
                """
                (
                    e.nome LIKE %s
                    OR e.serie LIKE %s
                    OR e.mac LIKE %s
                    OR pessoa.nome LIKE %s
                )
                """
            )

            params.extend([
                termo,
                termo,
                termo,
                termo,
            ])

        where_sql = ""

        if where:
            where_sql = "WHERE " + " AND ".join(where)

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        sql_total = f"""
            SELECT COUNT(*) AS total

            FROM parque_tecnologico e

            LEFT JOIN pessoa_bi pessoa
                ON pessoa.id = e.id_colaborador

            {where_sql}
        """

        cursor.execute(sql_total, tuple(params))

        resultado_total = cursor.fetchone()

        total = resultado_total["total"]

        # ----------------------------------------------------
        # DADOS
        # ----------------------------------------------------

        sql = f"""
            SELECT
                e.id,
                e.nome,
                e.id_empresa,
                e.id_tipo,
                e.id_departamento,
                e.id_marca,
                e.id_modelo,
                e.id_toner,
                e.id_monitor,
                e.id_colaborador,
                e.senha,
                e.scanner,
                e.data_fabricacao,
                e.serie,
                e.processador,
                e.memoria_ram,
                e.armazenamento,
                e.tamanho,
                e.so,
                e.ip,
                e.mac,
                e.observacao,
                e.ativo,

                emp.nome_empresa AS nome_empresa,
                tipo.nome AS nome_tipo,
                marca.nome AS nome_marca,
                modelo.nome AS nome_modelo,
                pessoa.nome AS nome_colaborador

            FROM parque_tecnologico e

            LEFT JOIN empresa_bi emp
                ON emp.codigo_empresa = e.id_empresa

            LEFT JOIN tipo_equipamento tipo
                ON tipo.id = e.id_tipo

            LEFT JOIN marca
                ON marca.id = e.id_marca

            LEFT JOIN modelo
                ON modelo.id = e.id_modelo

            LEFT JOIN pessoa_bi pessoa
                ON pessoa.id = e.id_colaborador

            {where_sql}

            ORDER BY e.nome

            LIMIT %s OFFSET %s
        """

        params_dados = params + [limit, skip]

        cursor.execute(sql, tuple(params_dados))

        itens = cursor.fetchall()

        itens = [
            _normalizar_equipamento(item)
            for item in itens
        ]

        return EquipamentoListaOut(
            total=total,
            itens=itens,
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# RESUMO

# ============================================================

@router.get(
"/resumo",
response_model=ResumoEquipamentos,
)
def resumo_equipamentos():


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        sql = """
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN ativo = 1 THEN 1
                        ELSE 0
                    END
                ) AS ativos,

                SUM(
                    CASE
                        WHEN ativo = 0 THEN 1
                        ELSE 0
                    END
                ) AS inativos,

                SUM(
                    CASE
                        WHEN ativo = 1
                        AND id_colaborador IS NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS sem_colaborador

            FROM parque_tecnologico
        """

        cursor.execute(sql)

        resumo = cursor.fetchone()

        # ----------------------------------------------------
        # POR TIPO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(tipo.nome, 'Sem tipo') AS nome_tipo,
                COUNT(*) AS quantidade

            FROM parque_tecnologico e

            LEFT JOIN tipo_equipamento tipo
                ON tipo.id = e.id_tipo

            WHERE e.ativo = 1

            GROUP BY tipo.nome

            ORDER BY quantidade DESC
            """
        )

        por_tipo_rows = cursor.fetchall()

        por_tipo = {
            row["nome_tipo"]: row["quantidade"]
            for row in por_tipo_rows
        }

        # ----------------------------------------------------
        # POR EMPRESA
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(emp.nome_empresa, 'Sem empresa') AS nome_empresa,
                COUNT(*) AS quantidade

            FROM parque_tecnologico e

            LEFT JOIN empresa_bi emp
                ON emp.codigo_empresa = e.id_empresa

            WHERE e.ativo = 1

            GROUP BY emp.nome_empresa

            ORDER BY quantidade DESC
            """
        )

        por_empresa_rows = cursor.fetchall()

        por_empresa = {
            row["nome_empresa"]: row["quantidade"]
            for row in por_empresa_rows
        }

        return ResumoEquipamentos(
            total=resumo["total"] or 0,
            ativos=resumo["ativos"] or 0,
            inativos=resumo["inativos"] or 0,
            sem_colaborador=resumo["sem_colaborador"] or 0,
            por_tipo=por_tipo,
            por_empresa=por_empresa,
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# OBTER POR ID

# ============================================================

@router.get(
"/{equipamento_id}",
response_model=EquipamentoOut,
)
def obter_equipamento(
equipamento_id: int
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        return _normalizar_equipamento(eq)

    finally:
        _fechar(conn, cursor)


# ============================================================

# HISTÓRICO

# ============================================================

@router.get(
"/{equipamento_id}/historico",
response_model=list[MovimentacaoOut],
)
def historico_equipamento(
equipamento_id: int
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        # Confirma existência
        _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        # ----------------------------------------------------
        # MOVIMENTAÇÕES
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                id_colaborador,
                data_vinculo,
                data_devolucao,
                observacao

            FROM equipamento_movimentacao

            WHERE tipo_ativo = 'equipamento'
            AND id_ativo = %s

            ORDER BY data_vinculo DESC
            """,
            (equipamento_id,),
        )

        movimentacoes = cursor.fetchall()

        if not movimentacoes:
            return []

        # ----------------------------------------------------
        # PESSOAS
        # ----------------------------------------------------

        ids_colaboradores = list({
            m["id_colaborador"]
            for m in movimentacoes
            if m["id_colaborador"] is not None
        })

        pessoas = {}

        if ids_colaboradores:

            placeholders = ", ".join(
                ["%s"] * len(ids_colaboradores)
            )

            cursor.execute(
                f"""
                SELECT
                    id,
                    nome

                FROM pessoa_bi

                WHERE id IN ({placeholders})
                """,
                tuple(ids_colaboradores),
            )

            pessoas_rows = cursor.fetchall()

            pessoas = {
                row["id"]: row["nome"]
                for row in pessoas_rows
            }

        # ----------------------------------------------------
        # RETORNO
        # ----------------------------------------------------

        return [
            MovimentacaoOut(
                id=m["id"],
                id_colaborador=m["id_colaborador"],
                nome_colaborador=pessoas.get(
                    m["id_colaborador"]
                ),
                data_vinculo=m["data_vinculo"],
                data_devolucao=m["data_devolucao"],
                observacao=m["observacao"],
            )
            for m in movimentacoes
        ]

    finally:
        _fechar(conn, cursor)


# ============================================================

# CRIAR

# ============================================================

@router.post(
"",
response_model=EquipamentoOut,
status_code=201,
)
def criar_equipamento(
payload: EquipamentoCreate
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        dados = payload.model_dump(
            exclude_unset=True
        )

        if not dados:
            raise HTTPException(
                status_code=400,
                detail="Nenhum dado informado",
            )

        # ----------------------------------------------------
        # CAMPOS PERMITIDOS
        # ----------------------------------------------------

        campos_permitidos = {
            "nome",
            "id_colaborador",
            "senha",
            "id_empresa",
            "id_departamento",
            "id_tipo",
            "id_monitor",
            "id_marca",
            "id_modelo",
            "id_toner",
            "scanner",
            "data_fabricacao",
            "serie",
            "processador",
            "memoria_ram",
            "armazenamento",
            "tamanho",
            "so",
            "ip",
            "mac",
            "observacao",
            "ativo",
        }

        dados = {
            campo: valor
            for campo, valor in dados.items()
            if campo in campos_permitidos
        }

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        if "ativo" not in dados:
            dados["ativo"] = 1

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        campos = list(dados.keys())

        colunas_sql = ", ".join(
            f"`{campo}`"
            for campo in campos
        )

        placeholders = ", ".join(
            ["%s"] * len(campos)
        )

        valores = [
            dados[campo]
            for campo in campos
        ]

        sql = f"""
            INSERT INTO parque_tecnologico
            ({colunas_sql})
            VALUES
            ({placeholders})
        """

        cursor.execute(
            sql,
            tuple(valores),
        )

        equipamento_id = cursor.lastrowid

        # ----------------------------------------------------
        # HISTÓRICO INICIAL
        # ----------------------------------------------------

        if dados.get("id_colaborador"):

            cursor.execute(
                """
                INSERT INTO equipamento_movimentacao
                (
                    tipo_ativo,
                    id_ativo,
                    id_colaborador,
                    data_vinculo
                )
                VALUES
                (
                    'equipamento',
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    equipamento_id,
                    dados["id_colaborador"],
                    datetime.now(),
                ),
            )

        conn.commit()

        # ----------------------------------------------------
        # RETORNO
        # ----------------------------------------------------

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        return _normalizar_equipamento(eq)

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar equipamento: {str(e)}",
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# ATUALIZAR

# ============================================================

@router.put(
"/{equipamento_id}",
response_model=EquipamentoOut,
)
def atualizar_equipamento(
equipamento_id: int,
payload: EquipamentoUpdate
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # EXISTÊNCIA
        # ----------------------------------------------------

        _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        dados = payload.model_dump(
            exclude_unset=True
        )

        if not dados:
            raise HTTPException(
                status_code=400,
                detail="Nenhum dado informado para atualização",
            )

        campos_permitidos = {
            "nome",
            "id_colaborador",
            "senha",
            "id_empresa",
            "id_departamento",
            "id_tipo",
            "id_monitor",
            "id_marca",
            "id_modelo",
            "id_toner",
            "scanner",
            "data_fabricacao",
            "serie",
            "processador",
            "memoria_ram",
            "armazenamento",
            "tamanho",
            "so",
            "ip",
            "mac",
            "observacao",
            "ativo",
        }

        dados = {
            campo: valor
            for campo, valor in dados.items()
            if campo in campos_permitidos
        }

        if not dados:
            raise HTTPException(
                status_code=400,
                detail="Nenhum campo válido informado",
            )

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        set_sql = ", ".join(
            f"`{campo}` = %s"
            for campo in dados.keys()
        )

        valores = list(dados.values())

        valores.append(equipamento_id)

        cursor.execute(
            f"""
            UPDATE parque_tecnologico

            SET {set_sql}

            WHERE id = %s
            """,
            tuple(valores),
        )

        conn.commit()

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        return _normalizar_equipamento(eq)

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar equipamento: {str(e)}",
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# EXCLUIR — SOFT DELETE

# ============================================================

@router.delete(
"/{equipamento_id}",
status_code=204,
)
def excluir_equipamento(
equipamento_id: int
):


    conn = connection_mysql()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT id
            FROM parque_tecnologico
            WHERE id = %s
            LIMIT 1
            """,
            (equipamento_id,),
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Equipamento não encontrado",
            )

        cursor.execute(
            """
            UPDATE parque_tecnologico
            SET ativo = 0
            WHERE id = %s
            """,
            (equipamento_id,),
        )

        conn.commit()

        return None

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir equipamento: {str(e)}",
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# VINCULAR COLABORADOR

# ============================================================

@router.post(
"/{equipamento_id}/vincular",
response_model=EquipamentoOut,
)
def vincular_colaborador(
equipamento_id: int,
payload: VincularRequest
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        # ----------------------------------------------------
        # COLABORADOR
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                nome

            FROM pessoa_bi

            WHERE id = %s

            LIMIT 1
            """,
            (payload.id_colaborador,),
        )

        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(
                status_code=404,
                detail="Colaborador não encontrado",
            )

        # ----------------------------------------------------
        # JÁ VINCULADO
        # ----------------------------------------------------

        if eq["id_colaborador"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Equipamento já está vinculado "
                    "a outro colaborador. "
                    "Devolva antes de vincular."
                ),
            )

        # ----------------------------------------------------
        # ATUALIZA EQUIPAMENTO
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parque_tecnologico

            SET id_colaborador = %s

            WHERE id = %s
            """,
            (
                payload.id_colaborador,
                equipamento_id,
            ),
        )

        # ----------------------------------------------------
        # HISTÓRICO
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO equipamento_movimentacao
            (
                tipo_ativo,
                id_ativo,
                id_colaborador,
                data_vinculo,
                observacao
            )
            VALUES
            (
                'equipamento',
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                equipamento_id,
                payload.id_colaborador,
                datetime.now(),
                payload.observacao,
            ),
        )

        conn.commit()

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        return _normalizar_equipamento(eq)

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao vincular colaborador: {str(e)}",
        )

    finally:
        _fechar(conn, cursor)


# ============================================================

# DEVOLVER EQUIPAMENTO

# ============================================================

@router.post(
"/{equipamento_id}/devolver",
response_model=EquipamentoOut,
)
def devolver_equipamento(
equipamento_id: int,
payload: DevolverRequest
):


    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        # ----------------------------------------------------
        # NÃO ESTÁ VINCULADO
        # ----------------------------------------------------

        if not eq["id_colaborador"]:
            raise HTTPException(
                status_code=400,
                detail="Equipamento não está vinculado a ninguém",
            )

        # ----------------------------------------------------
        # MOVIMENTAÇÃO ABERTA
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                observacao

            FROM equipamento_movimentacao

            WHERE tipo_ativo = 'equipamento'
            AND id_ativo = %s
            AND id_colaborador = %s
            AND data_devolucao IS NULL

            ORDER BY data_vinculo DESC

            LIMIT 1
            """,
            (
                equipamento_id,
                eq["id_colaborador"],
            ),
        )

        movimentacao = cursor.fetchone()

        if movimentacao:

            observacao = movimentacao["observacao"]

            if payload.observacao:
                observacao = payload.observacao

            cursor.execute(
                """
                UPDATE equipamento_movimentacao

                SET
                    data_devolucao = %s,
                    observacao = %s

                WHERE id = %s
                """,
                (
                    datetime.now(),
                    observacao,
                    movimentacao["id"],
                ),
            )

        # ----------------------------------------------------
        # REMOVE COLABORADOR
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parque_tecnologico

            SET id_colaborador = NULL

            WHERE id = %s
            """,
            (equipamento_id,),
        )

        conn.commit()

        eq = _get_equipamento_or_404(
            cursor,
            equipamento_id,
        )

        return _normalizar_equipamento(eq)

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao devolver equipamento: {str(e)}",
        )

    finally:
        _fechar(conn, cursor)