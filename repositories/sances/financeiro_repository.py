import logging
from datetime import datetime

from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger


logger = get_layer_logger("bronze", "financeiro_repository")


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BATCH_COMMIT = 500

# ============================================================
# FUNÇÃO ÚNICA DE COMPARAÇÃO DE DATA
# ============================================================

def data_mais_recente(data_nova, data_banco) -> bool:
    """
    Retorna True quando data_nova é mais recente que data_banco.

    Aceita:
        - datetime
        - string YYYY-MM-DD HH:MM:SS
        - string YYYY-MM-DD
        - string ISO
        - None

    Essa função é utilizada pelos UPDATES de:
        - financeiro_raw
        - financeiro_bi
        - recebimentos_raw
        - recebimentos_bi
    """

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
    """
    Salva uma página da API nas tabelas RAW.

    Fluxo:

        API
         ↓
        financeiro_raw
         ↓
        recebimentos_raw
    """

    recebimentos = recebimentos or []

    # --------------------------------------------------------
    # Garante tenant_id nos títulos
    # --------------------------------------------------------

    for item in itens:
        item["tenant_id"] = tenant_id

    # --------------------------------------------------------
    # Garante tenant_id nos recebimentos
    # --------------------------------------------------------

    for item in recebimentos:
        item["tenant_id"] = tenant_id

    # --------------------------------------------------------
    # Financeiro
    # --------------------------------------------------------

    resultado_titulos = upsert_financeiro_raw(itens)

    # --------------------------------------------------------
    # Recebimentos
    # --------------------------------------------------------

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

            # ------------------------------------------------
            # Validação
            # ------------------------------------------------

            if not codigo:
                ignorados += 1
                continue

            # ------------------------------------------------
            # Busca registro existente
            # ------------------------------------------------

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

            # =================================================
            # REGISTRO EXISTENTE
            # =================================================

            if existente:

                houve_alteracao = (
                    data_mais_recente(
                        item.get("data_alteracao"),
                        existente.get("data_alteracao"),
                    )
                    or
                    data_mais_recente(
                        item.get("data_baixa"),
                        existente.get("data_baixa"),
                    )
                    or
                    data_mais_recente(
                        item.get("data_insercao"),
                        existente.get("data_insercao"),
                    )
                    or
                    (
                        item.get("codigo_situacao")
                        is not None
                        and
                        item.get("codigo_situacao")
                        != existente.get("codigo_situacao")
                    )
                    
                )

                # ---------------------------------------------
                # Nada mudou
                # ---------------------------------------------

                if not houve_alteracao:
                    ignorados += 1
                    continue

            # =================================================
            # INSERT / UPDATE
            # =================================================

            colunas = list(item.keys())

            placeholders = [
                f"%({coluna})s"
                for coluna in colunas
            ]

            updates = [
                f"{coluna}=VALUES({coluna})"
                for coluna in colunas
                if coluna not in ("codigo", "tenant_id")
            ]

            sql = f"""
                INSERT INTO financeiro_raw (
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

                logger.error(
                    "Erro upsert financeiro_raw "
                    f"codigo={codigo}: {e}"
                )

            # ------------------------------------------------
            # Commit em lote
            # ------------------------------------------------

            if i % BATCH_COMMIT == 0:
                conn.commit()

        # ----------------------------------------------------
        # Commit final
        # ----------------------------------------------------

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
# RECEBIMENTOS RAW
# ============================================================

def upsert_financeiro_recebimento_raw(
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
    cursor = conn.cursor(dictionary=True)

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    try:

        for i, item in enumerate(registros, start=1):

            codigo_titulo = item.get("codigo_titulo")

            # ------------------------------------------------
            # Validação
            # ------------------------------------------------

            if not codigo_titulo:
                ignorados += 1
                continue

            # ------------------------------------------------
            # Busca existente
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    codigo_titulo,
                    data_alteracao
                FROM recebimentos_raw
                WHERE codigo_titulo = %s
                """,
                (codigo_titulo,),
            )

            existente = cursor.fetchone()

            # =================================================
            # EXISTENTE
            # =================================================

            if existente:

                houve_alteracao = data_mais_recente(
                    item.get("data_alteracao"),
                    existente.get("data_alteracao"),
                )

                if not houve_alteracao:
                    ignorados += 1
                    continue

            # =================================================
            # INSERT / UPDATE
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
                    "codigo_titulo",
                    "tenant_id",
                )
            ]

            sql = f"""
                INSERT INTO recebimentos_raw (
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

                logger.error(
                    "Erro upsert recebimentos_raw "
                    f"codigo_titulo={codigo_titulo}: {e}"
                )

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

            # ------------------------------------------------
            # IMPORTANTE:
            # A comparação abaixo é feita diretamente no SQL.
            # Não usamos a função Python aqui.
            # ------------------------------------------------

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

        logger.warning("upsert_financeiro_bi chamado com lista vazia — nada a gravar.")
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

                #logger.warning(f"Registro sem codigo_raw — ignorado: {item}")

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
                
                    atualizar = (
                        data_maior(item.get("data_alteracao"), existente.get("atualizado_em")) or
                        data_maior(item.get("data_baixa"), existente.get("data_baixa")) or
                        situacao(item.get("codigo_situacao"), existente.get("codigo_situacao"))
                    )

                    if not atualizar:
                        ignorados += 1
                        continue
                        
                    atualizados += 1
                else:
                    inseridos += 1

            except Exception as e:

                conn.rollback()

                erros += 1

                logger.error(
                    "Erro upsert financeiro_bi "
                    f"codigo_raw={codigo_raw}: {e}"
                )

            # ------------------------------------------------
            # Commit em lote
            # ------------------------------------------------

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    finally:

        cursor.close()
        conn.close()

    logger.info(
        f"financeiro_bi | INSERT={inseridos} UPDATE={atualizados} IGNORADOS={ignorados} ERRO={erros}"
    )
    return {"inseridos": inseridos, "atualizados": atualizados, "ignorados": ignorados, "erros": erros}
    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }


# ============================================================
# BUSCAR RECEBIMENTOS RAW
# ============================================================

def buscar_recebimentos_raw_para_transform() -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT rr.*
            FROM recebimentos_raw rr
            LEFT JOIN recebimentos_bi rb
                ON rb.codigo_raw = rr.codigo_titulo
            WHERE rb.codigo_raw IS NULL
               OR rr.data_alteracao > rb.atualizado_em
            ORDER BY rr.codigo_titulo ASC
            """
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conn.close()


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

    cursor_select = conn.cursor(dictionary=True)
    cursor_write = conn.cursor()

    inseridos = 0
    atualizados = 0
    ignorados = 0
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
            # Verifica se existe no BI
            # ------------------------------------------------

            cursor_select.execute(
                """
                SELECT
                    codigo_raw,
                    atualizado_em
                FROM recebimentos_bi
                WHERE codigo_raw = %s
                LIMIT 1
                """,
                (codigo_raw,),
            )

            existente = cursor_select.fetchone()


            if existente is None:
                pass

            # =================================================
            # REGISTRO EXISTENTE
            # =================================================

            if existente:

                houve_alteracao = data_mais_recente(
                    item.get("data_alteracao"),
                    existente.get("atualizado_em"),
                )

                if not houve_alteracao:

                    ignorados += 1

                    continue

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

                cursor_write.execute(sql, item)

                if existente:
                    atualizados += 1
                else:
                    inseridos += 1

            except Exception as e:

                conn.rollback()

                erros += 1

                logger.error(
                    "Erro upsert recebimentos_bi "
                    f"codigo_raw={codigo_raw}: {e}"
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()

        conn.commit()

    except Exception as e:

        conn.rollback()

        logger.exception(
            "Erro geral no upsert_recebimentos_bi: %s",
            e,
        )

        raise

    finally:

        try:
            cursor_select.close()
        except Exception:
            pass

        try:
            cursor_write.close()
        except Exception:
            pass

        try:
            conn.close()
        except Exception:
            pass

    return {
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }
