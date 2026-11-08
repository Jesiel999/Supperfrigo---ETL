import time

from database.mysql_connection import connection_mysql
from core.logger import get_layer_logger

logger = get_layer_logger("bronze", "estoque_veiculos_repository")

BATCH_COMMIT = 500

# Quantos erros de INSERT são logados com detalhe por chamada (o resto só conta).
MAX_ERROS_LOG = 5


def _resultado_vazio() -> dict:
    return {"inseridos": 0, "atualizados": 0, "ignorados": 0, "erros": 0}


# ============================================================
# UPSERT GENÉRICO
# ============================================================
# rowcount no MySQL com ON DUPLICATE KEY UPDATE:
#   1 = inseriu | 2 = atualizou | 0 = nada mudou (valores idênticos)
# Por isso não precisa de SELECT prévio por registro: se nada mudou, o
# MySQL não toca na linha (e a coluna ON UPDATE CURRENT_TIMESTAMP também não).
#
# Não há conn.rollback() por erro: uma falha em um único INSERT desfaz só
# aquele statement; o rollback() derrubaria também as linhas pendentes do lote.
#
# Logs:
#   DEBUG -> SQL gerado, primeiro registro, motivo de cada registro inválido
#   INFO  -> resumo de cada upsert (tabela, tempo, contadores)
#   ERROR -> os primeiros MAX_ERROS_LOG erros, mais a contagem do que foi omitido

def _upsert(
    tabela: str,
    registros: list[dict],
    chave: str,
    excluir_update: tuple,
    extra_update: str | None = None,
) -> dict:

    resultado = _resultado_vazio()

    if not registros:
        logger.debug(f"[{tabela}] upsert sem registros — nada a gravar")
        return resultado

    inicio = time.perf_counter()
    invalidos = 0

    colunas = list(registros[0].keys())
    placeholders = [f"%({c})s" for c in colunas]
    updates = [f"{c}=VALUES({c})" for c in colunas if c not in excluir_update]

    if extra_update:
        updates.append(extra_update)

    sql = f"""
        INSERT INTO {tabela} ({', '.join(colunas)})
        VALUES ({', '.join(placeholders)})
        ON DUPLICATE KEY UPDATE {', '.join(updates)}
    """

    logger.debug(f"[{tabela}] upsert iniciado: {len(registros)} registros, {len(colunas)} colunas")
    logger.debug(f"[{tabela}] SQL:\n{sql}")
    logger.debug(f"[{tabela}] primeiro registro: {registros[0]}")

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        for i, item in enumerate(registros, start=1):

            if item.get("tenant_id") is None or not item.get(chave):
                resultado["ignorados"] += 1
                invalidos += 1
                logger.debug(
                    f"[{tabela}] registro #{i} inválido "
                    f"(tenant_id={item.get('tenant_id')!r}, {chave}={item.get(chave)!r}) — ignorado"
                )
                continue

            try:
                if not conn.is_connected():
                    logger.warning(f"[{tabela}] conexão perdida no registro #{i}; reconectando")
                    conn.reconnect(attempts=3, delay=5)
                    cursor = conn.cursor()

                cursor.execute(sql, item)

                if cursor.rowcount == 1:
                    resultado["inseridos"] += 1
                elif cursor.rowcount == 0:
                    resultado["ignorados"] += 1
                else:
                    resultado["atualizados"] += 1

            except Exception as e:
                resultado["erros"] += 1
                if resultado["erros"] <= MAX_ERROS_LOG:
                    logger.error(
                        f"[{tabela}] erro no upsert {chave}={item.get(chave)} "
                        f"(registro #{i}): {type(e).__name__}: {e}"
                    )

            if i % BATCH_COMMIT == 0:
                conn.commit()
                logger.debug(f"[{tabela}] commit parcial: {i}/{len(registros)} registros")

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    omitidos = resultado["erros"] - MAX_ERROS_LOG
    if omitidos > 0:
        logger.error(f"[{tabela}] +{omitidos} erros omitidos deste upsert")

    logger.info(
        f"[{tabela}] upsert concluído em {time.perf_counter() - inicio:.2f}s | "
        f"recebidos={len(registros)} inseridos={resultado['inseridos']} "
        f"atualizados={resultado['atualizados']} "
        f"ignorados={resultado['ignorados']} (inválidos={invalidos}) "
        f"erros={resultado['erros']}"
    )

    return resultado


# ============================================================
# ESTOQUE RAW
# ============================================================

def salvar_pagina_raw(tenant_id: int, itens: list[dict]) -> dict:
    logger.debug(f"[salvar_pagina_raw] tenant={tenant_id} | {len(itens)} veículos na página")

    for item in itens:
        item["tenant_id"] = tenant_id

    return upsert_veiculo_estoque_raw(itens)


def upsert_veiculo_estoque_raw(registros: list[dict]) -> dict:
    return _upsert(
        tabela="veiculo_estoque_raw",
        registros=registros,
        chave="codigo",
        excluir_update=("tenant_id", "codigo"),
    )


# ============================================================
# BUSCAR RAW PARA TRANSFORM
# ============================================================

def buscar_raw_para_transform(
    tenant_id: int,
    somente_nao_transformados: bool = True,
) -> list[dict]:

    inicio = time.perf_counter()

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        if somente_nao_transformados:
            # - nunca transformado
            # - raw mudou depois da última transformação
            # - veículo ativo: sempre reprocessa (dias_estoque depende de "hoje")
            cursor.execute(
                """
                SELECT er.*
                FROM veiculo_estoque_raw er
                LEFT JOIN veiculo_estoque_bi eb
                    ON eb.tenant_id = er.tenant_id
                   AND eb.codigo_raw = er.codigo
                WHERE er.tenant_id = %s
                  AND (
                        eb.codigo_raw IS NULL
                     OR er.atualizado_raw_em > eb.processado_em
                     OR er.ativo_no_estoque = 1
                  )
                ORDER BY er.codigo ASC
                """,
                (tenant_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM veiculo_estoque_raw WHERE tenant_id = %s ORDER BY codigo ASC",
                (tenant_id,),
            )

        linhas = cursor.fetchall()

        logger.info(
            f"[veiculo_estoque_raw] {len(linhas)} registros para transformar "
            f"(tenant={tenant_id}, somente_nao_transformados={somente_nao_transformados}) "
            f"em {time.perf_counter() - inicio:.2f}s"
        )

        return linhas

    finally:
        cursor.close()
        conn.close()


# ============================================================
# ESTOQUE BI
# ============================================================

def upsert_veiculo_estoque_bi(registros: list[dict]) -> dict:
    # processado_em é carimbado explicitamente: sem isso, um upsert com valores
    # idênticos não mudaria a coluna e o registro voltaria a ser selecionado.
    return _upsert(
        tabela="veiculo_estoque_bi",
        registros=registros,
        chave="codigo_raw",
        excluir_update=("tenant_id", "codigo_raw"),
        extra_update="processado_em = NOW()",
    )