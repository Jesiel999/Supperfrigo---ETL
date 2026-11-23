import logging
from datetime import datetime

from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger
from core.metrics import log_resultado

logger_bronze = get_layer_logger("bronze", "financeiro_repository")
logger_silver = get_layer_logger("silver", "financeiro_repository")

BATCH_COMMIT = 500

# ============================================================
# BUSCAR DATAS DE MOVIMENTAÇÃO (para cálculo de dias_pagamento/recebimento)
# ============================================================

def buscar_datas_movimentacao_por_titulo(tenant_id: int) -> dict:
    """
    Retorna {codigo_titulo: data_movimentacao_mais_recente} a partir do raw
    de recebimentos, já disponível na Bronze antes mesmo do transform.
    """
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                codigo,
                MAX(data_movimentacao) AS data_movimentacao
            FROM brz_sances_financeiro_recebimento
            WHERE tenant_id = %s
            GROUP BY codigo
            """,
            (tenant_id,),
        )

        return {
            row["codigo"]: row["data_movimentacao"]
            for row in cursor.fetchall()
        }

    finally:
        cursor.close()
        conn.close()

# ============================================================
# BUSCAR DATAS MAIS RECENTE
# ============================================================

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

    resultado_titulos = upsert_brz_sances_financeiro_titulo(itens)

    resultado_recebimentos = upsert_financeiro_recebimento_raw(
        recebimentos
    )

    resultado_titulos["recebimentos"] = resultado_recebimentos

    return resultado_titulos

# ============================================================
# REMOVER RECEBIMENTOS
# ============================================================

SITUACOES_COM_RECEBIMENTO = {"BAIXADO", "BAIXADO PARCIAL"}

def _remover_recebimentos_titulo(conn, codigo_titulo) -> None:
    """Remove brz_sances_financeiro_recebimento e slv_financeiro_recebimento vinculados a um título
    que deixou de estar baixado/baixado parcial."""
    cursor_del = conn.cursor()
    try:
        cursor_del.execute(
            "DELETE FROM brz_sances_financeiro_recebimento WHERE codigo = %s",
            (codigo_titulo,),
        )
        cursor_del.execute(
            "DELETE FROM slv_financeiro_recebimento WHERE codigo_raw = %s",
            (codigo_titulo,),
        )
    finally:
        cursor_del.close()

# ============================================================
# FINANCEIRO RAW
# ============================================================

def upsert_brz_sances_financeiro_titulo(registros: list[dict]) -> dict:

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
                FROM brz_sances_financeiro_titulo
                WHERE codigo_origem = %s
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
                data_mais_recente(
                    item.get("data_vencimento"),
                    existente.get("data_vencimento") if existente else None
                )
                or
                data_mais_recente(
                    item.get("data_competencia"),
                    existente.get("data_competencia") if existente else None
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
                INSERT INTO brz_sances_financeiro_titulo ({', '.join(colunas)})
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

                    descricao_situacao = str(
                        item.get("descricao_situacao") or ""
                    ).strip().upper()

                    if descricao_situacao not in SITUACOES_COM_RECEBIMENTO:
                        try:
                            _remover_recebimentos_titulo(conn, codigo)
                        except Exception as e_del:
                            logger.error(
                                "Erro ao remover recebimentos do título "
                                f"codigo={codigo}: {e_del}"
                            )

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

            codigo_recebimento = item.get("codigo_recebimento")

            if not codigo_recebimento:
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
                INSERT INTO brz_sances_financeiro_recebimento ({', '.join(colunas)})
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

    logger_silver.info(
        "[FINANCEIRO] Iniciando busca Bronze para Silver | "
        "somente_nao_transformados=%s",
        somente_nao_transformados,
    )

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        if somente_nao_transformados:

            sql = """
                SELECT fr.*
                FROM brz_sances_financeiro_titulo fr
                LEFT JOIN slv_financeiro_titulo fb
                    ON fb.codigo_origem = fr.codigo
                WHERE fb.codigo_origem IS NULL
                   OR data_mais_recente
            """

            sql = """
                SELECT fr.*
                FROM brz_sances_financeiro_titulo fr
                LEFT JOIN slv_financeiro_titulo fb
                    ON fb.codigo_origem = fr.codigo
                WHERE fb.codigo_origem IS NULL
                OR fb.atualizado_em IS NULL
                OR fr.data_alteracao > fb.atualizado_em
                OR NOT (fr.data_baixa <=> fb.data_baixa)
                OR NOT (fr.data_vencimento <=> fb.data_vencimento)
                OR NOT (fr.data_competencia <=> fb.data_competencia)
                OR (
                        fr.codigo_situacao IS NOT NULL
                        AND NOT (fr.codigo_situacao <=> fb.codigo_situacao)
                )
                ORDER BY fr.codigo ASC;
            """

        else:

            sql = """
                SELECT *
                FROM brz_sances_financeiro_titulo
                ORDER BY codigo ASC
            """

        cursor.execute(sql)
        
        registros = cursor.fetchall()

        logger_silver.info(
            "[FINANCEIRO] Busca Bronze concluída | registros=%s",
            len(registros),
        )

        if not registros:
            logger_silver.warning(
                "[FINANCEIRO] Nenhum registro encontrado para transformação"
            )

        return registros

    except Exception:
        logger_silver.exception(
            "[FINANCEIRO] Erro ao buscar registros Bronze"
        )
        raise

    finally:
        cursor.close()
        conn.close()

# ============================================================
# FINANCEIRO BI
# ============================================================

def upsert_slv_financeiro_titulo(
    registros: list[dict],
) -> dict:

    if not registros:
        logger_silver.warning(
            "[FINANCEIRO] Silver títulos não executado: "
            "nenhum registro recebido"
        )
        return {
            "processados": 0,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
        }

    total = len(registros)

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    tenant_ids = sorted({
        item.get("tenant_id")
        for item in registros
        if item.get("tenant_id") is not None
    })

    logger_silver.info(
        "[FINANCEIRO] INICIANDO UPSERT SILVER TÍTULOS | "
        "tenants=%s | total=%s",
        tenant_ids,
        total,
    )

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        for i, item in enumerate(registros, start=1):

            codigo_origem = item.get("codigo_origem")
            pessoa_id = item.get("pessoa_id")
            tenant_id = item.get("tenant_id")

            if not codigo_origem:
                ignorados += 1

                logger_silver.warning(
                    "[FINANCEIRO] Título ignorado | "
                    "tenant_id=%s | codigo_origem ausente",
                    tenant_id,
                )
                continue

            try:
                if not conn.is_connected():
                    conn.reconnect(attempts=3, delay=5)

                # Verificar existência do título
                cursor.execute(
                    """
                    SELECT codigo_origem
                    FROM slv_financeiro_titulo
                    WHERE codigo_origem = %s
                    """,
                    (codigo_origem,),
                )

                existente = cursor.fetchone()

                # Validar relacionamento com pessoa
                if pessoa_id is not None:

                    cursor.execute(
                        """
                        SELECT 1
                        FROM slv_pessoa
                        WHERE codigo_sances = %s
                        LIMIT 1
                        """,
                        (pessoa_id,),
                    )

                    pessoa_existe = cursor.fetchone()

                    if not pessoa_existe:
                        erros += 1

                        logger_silver.error(
                            "[FINANCEIRO] FK inválida: pessoa "
                            "não encontrada na Silver | "
                            "tenant_id=%s | codigo_origem=%s | "
                            "pessoa_id=%s | registro=%s/%s",
                            tenant_id,
                            codigo_origem,
                            pessoa_id,
                            i,
                            total,
                        )
                        continue

                colunas = list(item.keys())

                placeholders = [
                    f"%({coluna})s"
                    for coluna in colunas
                ]

                updates = [
                    f"{coluna}=VALUES({coluna})"
                    for coluna in colunas
                    if coluna != "codigo_origem"
                ]

                sql = f"""
                    INSERT INTO slv_financeiro_titulo (
                        {', '.join(colunas)}
                    )
                    VALUES (
                        {', '.join(placeholders)}
                    )
                    ON DUPLICATE KEY UPDATE
                        {', '.join(updates)}
                """

                # Isolar cada registro para evitar rollback
                # de registros anteriores do mesmo lote.
                cursor.execute("SAVEPOINT sp_financeiro_titulo")

                try:
                    cursor.execute(sql, item)

                    if existente:
                        atualizados += 1
                    else:
                        inseridos += 1

                    cursor.execute(
                        "RELEASE SAVEPOINT sp_financeiro_titulo"
                    )

                except Exception:
                    cursor.execute(
                        "ROLLBACK TO SAVEPOINT sp_financeiro_titulo"
                    )
                    cursor.execute(
                        "RELEASE SAVEPOINT sp_financeiro_titulo"
                    )
                    raise

            except Exception:
                erros += 1

                logger_silver.exception(
                    "[FINANCEIRO] Erro no UPSERT Silver título | "
                    "tenant_id=%s | codigo_origem=%s | "
                    "registro=%s/%s",
                    tenant_id,
                    codigo_origem,
                    i,
                    total,
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()

                logger_silver.info(
                    "[FINANCEIRO] PROGRESSO SILVER TÍTULOS | "
                    "processados=%s/%s | inseridos=%s | "
                    "atualizados=%s | ignorados=%s | erros=%s",
                    i,
                    total,
                    inseridos,
                    atualizados,
                    ignorados,
                    erros,
                )

        conn.commit()

    except Exception:
        conn.rollback()

        logger_silver.exception(
            "[FINANCEIRO] Falha geral no processamento Silver"
        )
        raise

    finally:
        cursor.close()
        conn.close()

    resultado = {
        "processados": total,
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }

    logger_silver.info(
        "[FINANCEIRO] FINALIZADO UPSERT SILVER TÍTULOS | "
        "processados=%s | inseridos=%s | atualizados=%s | "
        "ignorados=%s | erros=%s",
        total,
        inseridos,
        atualizados,
        ignorados,
        erros,
    )

    log_resultado(
        "FINANCEIRO SILVER TÍTULOS",
        resultado,
        logger_silver,
    )

    return resultado

# ============================================================
# BUSCAR RECEBIMENTOS RAW
# ============================================================

def buscar_brz_sances_financeiro_recebimento_para_transform(
    tenant_id: int,
) -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT rr.*
            FROM brz_sances_financeiro_recebimento rr
            LEFT JOIN slv_financeiro_recebimento rb
                ON rb.tenant_id = rr.tenant_id
               AND rb.codigo_recebimento_raw = rr.codigo_recebimento

            WHERE rr.tenant_id = %s

              AND (
                    rb.codigo_raw IS NULL

                    OR rr.atualizado_em > rb.atualizado_em

                    OR (
                        rr.atualizado_em IS NULL
                        AND rb.codigo_raw IS NULL
                    )
              )

            ORDER BY rr.codigo_recebimento ASC
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

    logger_silver.info(
        "[FINANCEIRO] Iniciando transformação de recebimentos | "
        "tenant_id=%s | registros_entrada=%s",
        tenant_id,
        len(registros),
    )

    resultado = []

    for item in registros:

        codigo = item.get("codigo")

        if codigo is None:
            continue

        registro = {
            "tenant_id": tenant_id,
            "codigo_recebimento_raw": item.get("codigo_recebimento"),
            "codigo_raw": codigo,
            "codigo_tipo_movimentacao": item.get("codigo_tipo_movimentacao"),
            "descricao_tipo_movimentacao": item.get("descricao_tipo_movimentacao"),
            "valor_pago": item.get("valor_pago"),
            "valor_nominal": item.get("valor_nominal"),
            "data_movimentacao": item.get("data_movimentacao"),
            "codigo_conta": item.get("codigo_conta"),
            "descricao_conta": item.get("descricao_conta"),
            "historico": item.get("historico"),
            "data_conciliacao": item.get("data_conciliacao"),
            "codigo_caixa": item.get("codigo_caixa"),
            "codigo_cheque_terceiro": item.get("codigo_cheque_terceiro"),
            "codigo_pagamento_cartao": item.get("codigo_pagamento_cartao"),
            "desconto": item.get("desconto"),
            "acrescimo": item.get("acrescimo"),
            "juros": item.get("juros"),
            "multa": item.get("multa"),
            "data_alteracao": item.get("data_alteracao"),
        }

        resultado.append(registro)

    logger_silver.info(
        "[FINANCEIRO] Transformação de recebimentos concluída | "
        "tenant_id=%s | entrada=%s | saída=%s",
        tenant_id,
        len(registros),
        len(resultado),
    )

    return resultado

# ============================================================
# RECEBIMENTOS BI
# ============================================================

def upsert_slv_financeiro_recebimento(
    registros: list[dict],
) -> dict:

    if not registros:
        logger_silver.warning(
            "[FINANCEIRO] Silver recebimentos não executado: "
            "nenhum registro recebido"
        )
        return {
            "processados": 0,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
        }

    total = len(registros)

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = 0

    logger_silver.info(
        "[FINANCEIRO] INICIANDO UPSERT SILVER RECEBIMENTOS | "
        "total=%s",
        total,
    )

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        for i, item in enumerate(registros, start=1):

            tenant_id = item.get("tenant_id")
            codigo = item.get("codigo_recebimento_raw")
            codigo_raw = item.get("codigo_raw")

            if tenant_id is None or codigo is None or codigo_raw is None:
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
                if coluna not in (
                    "tenant_id",
                    "codigo",
                    "codigo_raw",
                )
            ]

            sql = f"""
                INSERT INTO slv_financeiro_recebimento (
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
                    conn.reconnect(attempts=3, delay=5)

                cursor.execute(
                    "SAVEPOINT sp_financeiro_recebimento"
                )

                try:
                    cursor.execute(sql, item)

                    if cursor.rowcount == 1:
                        inseridos += 1
                    elif cursor.rowcount == 2:
                        atualizados += 1
                    else:
                        ignorados += 1

                    cursor.execute(
                        "RELEASE SAVEPOINT sp_financeiro_recebimento"
                    )

                except Exception:
                    cursor.execute(
                        "ROLLBACK TO SAVEPOINT sp_financeiro_recebimento"
                    )
                    cursor.execute(
                        "RELEASE SAVEPOINT sp_financeiro_recebimento"
                    )
                    raise

            except Exception:
                erros += 1

                logger_silver.exception(
                    "[FINANCEIRO] Erro UPSERT recebimento | "
                    "tenant_id=%s | codigo_recebimento=%s | "
                    "codigo_raw=%s | registro=%s/%s",
                    tenant_id,
                    codigo,
                    codigo_raw,
                    i,
                    total,
                )

            if i % BATCH_COMMIT == 0:
                conn.commit()

                logger_silver.info(
                    "[FINANCEIRO] PROGRESSO SILVER RECEBIMENTOS | "
                    "processados=%s/%s | inseridos=%s | "
                    "atualizados=%s | ignorados=%s | erros=%s",
                    i,
                    total,
                    inseridos,
                    atualizados,
                    ignorados,
                    erros,
                )

        conn.commit()

    except Exception:
        conn.rollback()

        logger_silver.exception(
            "[FINANCEIRO] Falha geral no UPSERT recebimentos"
        )
        raise

    finally:
        cursor.close()
        conn.close()

    resultado = {
        "processados": total,
        "inseridos": inseridos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "erros": erros,
    }

    logger_silver.info(
        "[FINANCEIRO] FINALIZADO UPSERT SILVER RECEBIMENTOS | "
        "processados=%s | inseridos=%s | atualizados=%s | "
        "ignorados=%s | erros=%s",
        total,
        inseridos,
        atualizados,
        ignorados,
        erros,
    )

    log_resultado(
        "FINANCEIRO SILVER RECEBIMENTOS",
        resultado,
        logger_silver,
    )

    return resultado
