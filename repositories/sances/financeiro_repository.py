import logging
from datetime import datetime

from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "financeiro_repository")

BATCH_COMMIT = 500

def data_mais_recente(data_nova, data_banco) -> bool:

    def converter(valor):
        if valor is None:
            return None

        if isinstance(valor, datetime):
            return valor

        if isinstance(valor, str):
            valor = valor.strip()

            if not valor:
                return None

            formatos = (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            )

            for formato in formatos:
                try:
                    return datetime.strptime(valor, formato)
                except ValueError:
                    continue

        return None

    nova = converter(data_nova)
    antiga = converter(data_banco)

    if nova is None:
        return False

    if antiga is None:
        return True

    return nova > antiga


# ============================================================
# SALVAR PÁGINA COMPLETA
# ============================================================

def salvar_pagina_raw(
    tenant_id: int,
    itens: list[dict],
    recebimentos: list[dict] | None = None,
) -> dict:

    recebimentos = recebimentos or []

    for item in itens:
        item["tenant_id"] = tenant_id

    for item in recebimentos:
        item["tenant_id"] = tenant_id

    resultado_titulos = upsert_financeiro_raw(itens)

    resultado_recebimentos = upsert_financeiro_recebimento_raw(
        recebimentos
    )

    resultado_titulos["recebimentos"] = resultado_recebimentos

    return resultado_titulos


# ============================================================
# FINANCEIRO RAW
# ============================================================

def upsert_financeiro_raw(registros: list[dict]) -> dict:

    if not registros:
        return {
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
        }

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    try:

        for i, item in enumerate(registros, start=1):

            codigo = item.get("codigo")

            if not codigo:
                ignorados += 1
                continue

            cursor.execute(
                """
                SELECT
                    codigo,
                    data_alteracao,
                    data_baixa,
                    data_insercao,
                    codigo_situacao
                FROM financeiro_raw
                WHERE codigo = %s
                """,
                (codigo,),
            )
            existente = cursor.fetchone()

            houve_alteracao = (
                data_mais_recente(
                    item.get("data_alteracao"),
                    existente.get("data_alteracao") if existente else None
                )
                or
                data_mais_recente(
                    item.get("data_baixa"),
                    existente.get("data_baixa") if existente else None
                )
                or
                (
                    item.get("codigo_situacao") is not None
                    and existente is not None
                    and item.get("codigo_situacao")
                    != existente.get("codigo_situacao")
                )
            )

            # Se já existe e não houve alteração relevante, não precisa fazer upsert
            if existente and not houve_alteracao:
                ignorados += 1
                continue

            acao = "UPDATE" if existente else "INSERT"

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [f"{c}=VALUES({c})" for c in colunas if c != "codigo"]

            sql = f"""
                INSERT INTO financeiro_raw ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """

            try:

                if not conn.is_connected():
                    conn.reconnect(
                        attempts=3,
                        delay=5,
                    )

                cursor.execute(sql, item)

                if acao == "INSERT":
                    inseridos += 1
                else:
                    atualizados += 1

            except Exception as e:

                conn.rollback()

                erros += 1

            # ------------------------------------------------
            # Commit em lote
            # ------------------------------------------------

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }

# ============================================================
# FINANCEIRO RECEBIMENTO RAW
# ============================================================

def upsert_financeiro_recebimento_raw(registros: list[dict]) -> dict:

    if not registros:
        return {
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
        }

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    try:

        for i, item in enumerate(registros, start=1):

            codigo = item.get("codigo")

            if not codigo:
                ignorados += 1
                continue

            colunas      = list(item.keys())
            placeholders = [f"%({c})s" for c in colunas]
            updates      = [
                f"{c}=VALUES({c})"
                for c in colunas
                if c not in ("codigo",)
            ]

            sql = f"""
                INSERT INTO recebimentos_raw ({', '.join(colunas)})
                VALUES ({', '.join(placeholders)})
                ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """

            try:

                if not conn.is_connected():
                    conn.reconnect(
                        attempts=3,
                        delay=5,
                    )

                cursor.execute(sql, item)

                if cursor.rowcount == 1:
                    inseridos += 1
                else:
                    atualizados += 1

            except Exception as e:

                conn.rollback()

                erros += 1

            # ------------------------------------------------
            # Commit em lote
            # ------------------------------------------------

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }

    
# ============================================================
# BUSCAR FINANCEIRO RAW
# ============================================================

def buscar_raw_para_transform(
    somente_nao_transformados: bool = True,
) -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        if somente_nao_transformados:

            sql = """
                SELECT fr.*
                FROM financeiro_raw fr
                LEFT JOIN financeiro_bi fb
                    ON fb.codigo_raw = fr.codigo
                WHERE fb.codigo_raw IS NULL
                   OR data_mais_recente
            """

            sql = """
                SELECT fr.*
                FROM financeiro_raw fr
                LEFT JOIN financeiro_bi fb
                    ON fb.codigo_raw = fr.codigo
                WHERE fb.codigo_raw IS NULL
                   OR fr.data_alteracao > fb.atualizado_em
                   OR fr.data_baixa > fb.data_baixa
                   OR (
                        fr.codigo_situacao IS NOT NULL
                        AND fr.codigo_situacao <> fb.codigo_situacao
                   )
                ORDER BY fr.codigo ASC
            """

        else:

            sql = """
                SELECT *
                FROM financeiro_raw
                ORDER BY codigo ASC
            """

        cursor.execute(sql)

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


# ============================================================
# FINANCEIRO BI
# ============================================================

def upsert_financeiro_bi(
    registros: list[dict],
) -> dict:

    if not registros:

        return {"inseridos": 0, "atualizados": 0, "ignorados": 0, "erros": 0}

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    ignorados = 0

    erros       = 0
    BATCH_COMMIT = 500

    erros = 0

    try:

        for i, item in enumerate(registros, start=1):

            codigo_raw = item.get("codigo_raw")

            # ------------------------------------------------
            # Validação
            # ------------------------------------------------

            if not codigo_raw:

                ignorados += 1
                continue

            # ------------------------------------------------
            # Busca existente
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    codigo_raw,
                    atualizado_em,
                    data_baixa,
                    codigo_situacao
                FROM financeiro_bi
                WHERE codigo_raw = %s
                """,
                (codigo_raw,),
            )

            existente = cursor.fetchone()

            # =================================================
            # EXISTENTE
            # =================================================

            if existente:

                houve_alteracao = (
                    data_mais_recente(
                        item.get("data_alteracao"),
                        existente.get("atualizado_em"),
                    )
                    or
                    data_mais_recente(
                        item.get("data_baixa"),
                        existente.get("data_baixa"),
                    )
                    or
                    (
                        item.get("codigo_situacao") is not None
                        and
                        item.get("codigo_situacao")
                        != existente.get("codigo_situacao")
                    )
                )

                if not houve_alteracao:

                    ignorados += 1

                    continue

            # =================================================
            # UPSERT
            # =================================================

            colunas = list(item.keys())

            placeholders = [
                f"%({coluna})s"
                for coluna in colunas
            ]

            updates = [
                f"{coluna}=VALUES({coluna})"
                for coluna in colunas
                if coluna != "codigo_raw"
            ]

            sql = f"""
                INSERT INTO financeiro_bi (
                    {', '.join(colunas)}
                )
                VALUES (
                    {', '.join(placeholders)}
                )
                ON DUPLICATE KEY UPDATE
                    {', '.join(updates)}
            """

            try:

                if not conn.is_connected():
                    conn.reconnect(
                        attempts=3,
                        delay=5,
                    )

                cursor.execute(sql, item)

                if existente:
                    atualizados += 1
                else:
                    inseridos += 1

            except Exception as e:

                conn.rollback()

                erros += 1

            # ------------------------------------------------
            # Commit em lote
            # ------------------------------------------------

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    return {"inseridos": inseridos, "atualizados": atualizados, "ignorados": ignorados, "erros": erros}



# ============================================================
# BUSCAR RECEBIMENTOS RAW
# ============================================================

def buscar_recebimentos_raw_para_transform(
    tenant_id: int,
) -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT rr.*
            FROM recebimentos_raw rr
            LEFT JOIN recebimentos_bi rb
                ON rb.tenant_id = rr.tenant_id
               AND rb.codigo_raw = rr.codigo

            WHERE rr.tenant_id = %s

              AND (
                    rb.codigo_raw IS NULL

                    OR rr.data_alteracao > rb.atualizado_em

                    OR (
                        rr.data_alteracao IS NULL
                        AND rb.codigo_raw IS NULL
                    )
              )

            ORDER BY rr.codigo ASC
            """,
            (tenant_id,),
        )

        registros = cursor.fetchall()

        return registros

    finally:

        cursor.close()
        conn.close()

# ============================================================
# TRANSFORMAR RECEBIMENTOS BI
# ============================================================


def transformar_recebimentos(
    registros: list[dict],
    tenant_id: int,
) -> list[dict]:

    resultado = []

    for item in registros:

        codigo = item.get("codigo")

        if codigo is None:
            continue

        registro = {
            "tenant_id": tenant_id,
            "codigo_raw": codigo,

            "codigo_tipo_movimentacao":
                item.get("codigo_tipo_movimentacao"),

            "descricao_tipo_movimentacao":
                item.get("descricao_tipo_movimentacao"),

            "valor_pago":
                item.get("valor_pago"),

            "valor_nominal":
                item.get("valor_nominal"),

            "data_movimentacao":
                item.get("data_movimentacao"),

            "codigo_conta":
                item.get("codigo_conta"),

            "descricao_conta":
                item.get("descricao_conta"),

            "historico":
                item.get("historico"),

            "data_conciliacao":
                item.get("data_conciliacao"),

            "codigo_caixa":
                item.get("codigo_caixa"),

            "codigo_cheque_terceiro":
                item.get("codigo_cheque_terceiro"),

            "codigo_pagamento_cartao":
                item.get("codigo_pagamento_cartao"),

            "desconto":
                item.get("desconto"),

            "acrescimo":
                item.get("acrescimo"),

            "juros":
                item.get("juros"),

            "multa":
                item.get("multa"),

            "data_alteracao":
                item.get("data_alteracao"),
        }

        resultado.append(registro)

    return resultado

# ============================================================
# RECEBIMENTOS BI
# ============================================================

def upsert_recebimentos_bi(
    registros: list[dict],
) -> dict:

    if not registros:

        return {
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
        }

    conn = connection_mysql()
    cursor = conn.cursor()

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    try:

        for i, item in enumerate(registros, start=1):

            tenant_id = item.get("tenant_id")
            codigo_raw = item.get("codigo_raw")

            # =================================================
            # VALIDAÇÃO
            # =================================================

            if tenant_id is None:

                ignorados += 1

                continue

            if codigo_raw is None:

                ignorados += 1

                continue

            # =================================================
            # COLUNAS
            # =================================================

            colunas = list(item.keys())

            placeholders = [
                f"%({coluna})s"
                for coluna in colunas
            ]

            updates = [
                f"{coluna}=VALUES({coluna})"
                for coluna in colunas
                if coluna not in (
                    "tenant_id",
                    "codigo_raw",
                )
            ]

            # =================================================
            # UPSERT
            # =================================================

            sql = f"""
                INSERT INTO recebimentos_bi (
                    {', '.join(colunas)}
                )
                VALUES (
                    {', '.join(placeholders)}
                )
                ON DUPLICATE KEY UPDATE
                    {', '.join(updates)}
            """

            try:

                if not conn.is_connected():

                    conn.reconnect(
                        attempts=3,
                        delay=5,
                    )

                cursor.execute(sql, item)

                if cursor.rowcount == 1:

                    inseridos += 1

                elif cursor.rowcount == 2:

                    atualizados += 1

                elif cursor.rowcount == 0:

                    ignorados += 1

            except Exception as e:

                conn.rollback()

                erros += 1

            # =================================================
            # COMMIT
            # =================================================

            if i % BATCH_COMMIT == 0:

                conn.commit()

        conn.commit()

    except Exception as e:

        conn.rollback()

        raise

    finally:

        cursor.close()
        conn.close()    

    resultado = {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }

    return resultado