from fastapi import APIRouter, Depends, HTTPException

from database.mysql_connection import connection_mysql

from api.routers.schemas.equipamento import EquipamentoOut
from api.routers.schemas.chip import ChipOut
from auth.router import get_current_user


router = APIRouter(
    prefix="/api/colaboradores",
    tags=["Colaboradores"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/{colaborador_id}/equipamentos",
    response_model=list[EquipamentoOut]
)
def equipamentos_do_colaborador(
    colaborador_id: int,
    conn=Depends(connection_mysql)
):
    cursor = conn.cursor(dictionary=True)

    try:
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
        """, (colaborador_id,))

        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(
                status_code=404,
                detail="Colaborador não encontrado"
            )

        # ---------------------------------------------------------
        # Busca equipamentos
        # ---------------------------------------------------------
        cursor.execute("""
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
                t.nome AS nome_tipo,
                m.nome AS nome_marca,
                mo.nome AS nome_modelo

            FROM parque_tecnologico e

            LEFT JOIN empresa_bi emp
                ON emp.codigo_empresa = e.id_empresa

            LEFT JOIN tipo_equipamento t
                ON t.id = e.id_tipo

            LEFT JOIN marca m
                ON m.id = e.id_marca

            LEFT JOIN modelo mo
                ON mo.id = e.id_modelo

            WHERE e.id_colaborador = %s
              AND e.ativo = 1

            ORDER BY e.nome
        """, (colaborador_id,))

        equipamentos = cursor.fetchall()

        return [
            EquipamentoOut(
                id=eq["id"],
                nome=eq["nome"],
                id_empresa=eq["id_empresa"],
                id_tipo=eq["id_tipo"],
                id_departamento=eq["id_departamento"],
                id_marca=eq["id_marca"],
                id_modelo=eq["id_modelo"],
                id_toner=eq["id_toner"],
                id_monitor=eq["id_monitor"],
                id_colaborador=eq["id_colaborador"],
                senha=eq["senha"],
                scanner=eq["scanner"],
                data_fabricacao=eq["data_fabricacao"],
                serie=eq["serie"],
                processador=eq["processador"],
                memoria_ram=eq["memoria_ram"],
                armazenamento=eq["armazenamento"],
                tamanho=eq["tamanho"],
                so=eq["so"],
                ip=eq["ip"],
                mac=eq["mac"],
                observacao=eq["observacao"],
                ativo=eq["ativo"],
                nome_empresa=eq["nome_empresa"],
                nome_tipo=eq["nome_tipo"],
                nome_marca=eq["nome_marca"],
                nome_modelo=eq["nome_modelo"],
                nome_colaborador=colaborador["nome"],
            )
            for eq in equipamentos
        ]

    finally:
        cursor.close()
        conn.close()


@router.get(
    "/{colaborador_id}/chips",
    response_model=list[ChipOut]
)
def chips_do_colaborador(
    colaborador_id: int,
    conn=Depends(connection_mysql)
):
    cursor = conn.cursor(dictionary=True)

    try:
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
        """, (colaborador_id,))

        colaborador = cursor.fetchone()

        if not colaborador:
            raise HTTPException(
                status_code=404,
                detail="Colaborador não encontrado"
            )

        # ---------------------------------------------------------
        # Busca chips
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                c.id,
                c.id_empresa,
                c.id_departamento,
                c.id_colaborador,
                c.numero,
                c.iccid,

                emp.nome_empresa AS nome_empresa

            FROM chip c

            LEFT JOIN empresa_bi emp
                ON emp.codigo_empresa = c.id_empresa

            WHERE c.id_colaborador = %s

            ORDER BY c.numero
        """, (colaborador_id,))

        chips = cursor.fetchall()

        return [
            ChipOut(
                id=chip["id"],
                id_empresa=chip["id_empresa"],
                id_departamento=chip["id_departamento"],
                id_colaborador=chip["id_colaborador"],
                numero=chip["numero"],
                iccid=chip["iccid"],
                nome_colaborador=colaborador["nome"],
                nome_empresa=chip["nome_empresa"],
            )
            for chip in chips
        ]

    finally:
        cursor.close()
        conn.close()