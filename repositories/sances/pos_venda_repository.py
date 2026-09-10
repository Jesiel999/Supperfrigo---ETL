import logging
from datetime import datetime
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


# ==========================================
# HELPERS DE DATA
# ==========================================

def _converter_data_iso(valor) -> datetime | None:
    """Converte datas ISO com offset, ex: '2026-02-04T17:42:44.000-03:00'."""
    if not valor:
        return None
    try:
        v = str(valor).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _converter_data_br(valor) -> str | None:
    """Converte 'DD/MM/YYYY' (vencimento_parcela) para 'YYYY-MM-DD'."""
    if not valor:
        return None
    try:
        return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        # logger.warning(f"vencimento_parcela em formato inesperado: {valor}")
        return None


# ==========================================
# BRONZE — grava página inteira (pai + filhos)
# ==========================================

def salvar_pagina_raw(tenant_id: int, offset_pagina: int, itens: list[dict]) -> None:
    if not itens:
        return

    agora = datetime.now()
    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        codigos_origem = []

        for item in itens:
            codigo_origem = item.get("codigo")
            if not codigo_origem:
                continue
            codigos_origem.append(codigo_origem)

            cursor.execute(
                """
                INSERT INTO pos_venda_raw (
                    tenant_id, codigo_origem, tipo, descricao_tipo, orcamento_os,
                    numero, codigo_situacao, situacao, aguardando_liberacao,
                    codigo_empresa, nome_empresa, codigo_cliente, nome_cliente,
                    codigo_tipo_preco, descricao_tipo_preco, codigo_veiculo, placa_veiculo,
                    codigo_modelo_veiculo, descricao_modelo_veiculo, codigo_cor_veiculo,
                    descricao_cor_veiculo, ano_fabricacao_veiculo, ano_modelo_veiculo,
                    codigo_tipo_os, descricao_tipo_os, km_entrada, km_saida,
                    data_entrada, data_saida, solicitacao_cliente, avaria, defeito_averiguado,
                    codigo_proprietario, nome_proprietario, codigo_tipo_midia, descricao_tipo_midia,
                    codigo_modalidade_venda, descricao_modalidade_venda, codigo_conveniado,
                    nome_conveniado, codigo_consultor, nome_consultor,
                    percentual_comissao_peca, valor_comissao_peca_consultor,
                    percentual_comissao_servico, valor_comissao_servico_consultor,
                    total_comissao_consultor, observacao, observacao_nota,
                    codigo_usuario_insercao, nome_usuario_insercao, data_insercao,
                    codigo_usuario_alteracao, nome_usuario_alteracao, data_alteracao,
                    codigo_usuario_cancelamento, nome_usuario_cancelamento, data_cancelamento,
                    codigo_usuario_fechamento, nome_usuario_fechamento, data_fechamento,
                    valor_seguro, valor_frete, valor_despesas, valor_acrescimo_financeiro,
                    total_pecas_bruto, total_desconto_pecas, total_pecas_liquido,
                    total_pecas_custo, total_pecas_lucro,
                    total_servicos_bruto, total_desconto_servicos, total_servicos_liquido,
                    total_servicos_custo, total_servicos_lucro, total_geral,
                    codigo_condicao_pagamento, descricao_condicao_pagamento,
                    atualizado_em, processado_em
                ) VALUES (
                    %s,%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,
                    %s,%s,%s, %s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,%s,
                    %s,%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s, %s,%s, %s,%s,%s,
                    %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,
                    %s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,
                    %s, NULL
                )
                ON DUPLICATE KEY UPDATE
                    tipo=VALUES(tipo), descricao_tipo=VALUES(descricao_tipo), orcamento_os=VALUES(orcamento_os),
                    numero=VALUES(numero), codigo_situacao=VALUES(codigo_situacao), situacao=VALUES(situacao),
                    aguardando_liberacao=VALUES(aguardando_liberacao),
                    codigo_empresa=VALUES(codigo_empresa), nome_empresa=VALUES(nome_empresa),
                    codigo_cliente=VALUES(codigo_cliente), nome_cliente=VALUES(nome_cliente),
                    codigo_tipo_preco=VALUES(codigo_tipo_preco), descricao_tipo_preco=VALUES(descricao_tipo_preco),
                    codigo_veiculo=VALUES(codigo_veiculo), placa_veiculo=VALUES(placa_veiculo),
                    codigo_modelo_veiculo=VALUES(codigo_modelo_veiculo),
                    descricao_modelo_veiculo=VALUES(descricao_modelo_veiculo),
                    codigo_cor_veiculo=VALUES(codigo_cor_veiculo), descricao_cor_veiculo=VALUES(descricao_cor_veiculo),
                    ano_fabricacao_veiculo=VALUES(ano_fabricacao_veiculo), ano_modelo_veiculo=VALUES(ano_modelo_veiculo),
                    codigo_tipo_os=VALUES(codigo_tipo_os), descricao_tipo_os=VALUES(descricao_tipo_os),
                    km_entrada=VALUES(km_entrada), km_saida=VALUES(km_saida),
                    data_entrada=VALUES(data_entrada), data_saida=VALUES(data_saida),
                    solicitacao_cliente=VALUES(solicitacao_cliente), avaria=VALUES(avaria),
                    defeito_averiguado=VALUES(defeito_averiguado),
                    codigo_proprietario=VALUES(codigo_proprietario), nome_proprietario=VALUES(nome_proprietario),
                    codigo_tipo_midia=VALUES(codigo_tipo_midia), descricao_tipo_midia=VALUES(descricao_tipo_midia),
                    codigo_modalidade_venda=VALUES(codigo_modalidade_venda),
                    descricao_modalidade_venda=VALUES(descricao_modalidade_venda),
                    codigo_conveniado=VALUES(codigo_conveniado), nome_conveniado=VALUES(nome_conveniado),
                    codigo_consultor=VALUES(codigo_consultor), nome_consultor=VALUES(nome_consultor),
                    percentual_comissao_peca=VALUES(percentual_comissao_peca),
                    valor_comissao_peca_consultor=VALUES(valor_comissao_peca_consultor),
                    percentual_comissao_servico=VALUES(percentual_comissao_servico),
                    valor_comissao_servico_consultor=VALUES(valor_comissao_servico_consultor),
                    total_comissao_consultor=VALUES(total_comissao_consultor),
                    observacao=VALUES(observacao), observacao_nota=VALUES(observacao_nota),
                    codigo_usuario_insercao=VALUES(codigo_usuario_insercao),
                    nome_usuario_insercao=VALUES(nome_usuario_insercao), data_insercao=VALUES(data_insercao),
                    codigo_usuario_alteracao=VALUES(codigo_usuario_alteracao),
                    nome_usuario_alteracao=VALUES(nome_usuario_alteracao), data_alteracao=VALUES(data_alteracao),
                    codigo_usuario_cancelamento=VALUES(codigo_usuario_cancelamento),
                    nome_usuario_cancelamento=VALUES(nome_usuario_cancelamento),
                    data_cancelamento=VALUES(data_cancelamento),
                    codigo_usuario_fechamento=VALUES(codigo_usuario_fechamento),
                    nome_usuario_fechamento=VALUES(nome_usuario_fechamento), data_fechamento=VALUES(data_fechamento),
                    valor_seguro=VALUES(valor_seguro), valor_frete=VALUES(valor_frete),
                    valor_despesas=VALUES(valor_despesas), valor_acrescimo_financeiro=VALUES(valor_acrescimo_financeiro),
                    total_pecas_bruto=VALUES(total_pecas_bruto), total_desconto_pecas=VALUES(total_desconto_pecas),
                    total_pecas_liquido=VALUES(total_pecas_liquido), total_pecas_custo=VALUES(total_pecas_custo),
                    total_pecas_lucro=VALUES(total_pecas_lucro),
                    total_servicos_bruto=VALUES(total_servicos_bruto), total_desconto_servicos=VALUES(total_desconto_servicos),
                    total_servicos_liquido=VALUES(total_servicos_liquido), total_servicos_custo=VALUES(total_servicos_custo),
                    total_servicos_lucro=VALUES(total_servicos_lucro), total_geral=VALUES(total_geral),
                    codigo_condicao_pagamento=VALUES(codigo_condicao_pagamento),
                    descricao_condicao_pagamento=VALUES(descricao_condicao_pagamento),
                    atualizado_em=VALUES(atualizado_em),
                    processado_em=NULL
                """,
                (
                    tenant_id, codigo_origem, item.get("tipo"), item.get("descricao_tipo"), item.get("orcamento_os"),
                    item.get("numero"), item.get("codigo_situacao"), item.get("situacao"), item.get("aguardando_liberacao"),
                    item.get("codigo_empresa"), item.get("nome_empresa"), item.get("codigo_cliente"), item.get("nome_cliente"),
                    item.get("codigo_tipo_preco"), item.get("descricao_tipo_preco"), item.get("codigo_veiculo"), item.get("placa_veiculo"),
                    item.get("codigo_modelo_veiculo"), item.get("descricao_modelo_veiculo"), item.get("codigo_cor_veiculo"),
                    item.get("descricao_cor_veiculo"), item.get("ano_fabricacao_veiculo"), item.get("ano_modelo_veiculo"),
                    item.get("codigo_tipo_os"), item.get("descricao_tipo_os"), item.get("km_entrada"), item.get("km_saida"),
                    _converter_data_iso(item.get("data_entrada")), _converter_data_iso(item.get("data_saida")),
                    item.get("solicitacao_cliente"), item.get("avaria"), item.get("defeito_averiguado"),
                    item.get("codigo_proprietario"), item.get("nome_proprietario"), item.get("codigo_tipo_midia"), item.get("descricao_tipo_midia"),
                    item.get("codigo_modalidade_venda"), item.get("descricao_modalidade_venda"), item.get("codigo_conveniado"),
                    item.get("nome_conveniado"), item.get("codigo_consultor"), item.get("nome_consultor"),
                    item.get("percentual_comissao_peca"), item.get("valor_comissao_peca_consultor"),
                    item.get("percentual_comissao_servico"), item.get("valor_comissao_servico_consultor"),
                    item.get("total_comissao_consultor"), item.get("observacao"), item.get("observacao_nota"),
                    item.get("codigo_usuario_insercao"), item.get("nome_usuario_insercao"), _converter_data_iso(item.get("data_insercao")),
                    item.get("codigo_usuario_alteracao"), item.get("nome_usuario_alteracao"), _converter_data_iso(item.get("data_alteracao")),
                    item.get("codigo_usuario_cancelamento"), item.get("nome_usuario_cancelamento"), _converter_data_iso(item.get("data_cancelamento")),
                    item.get("codigo_usuario_fechamento"), item.get("nome_usuario_fechamento"), _converter_data_iso(item.get("data_fechamento")),
                    item.get("valor_seguro"), item.get("valor_frete"), item.get("valor_despesas"), item.get("valor_acrescimo_financeiro"),
                    item.get("total_pecas_bruto"), item.get("total_desconto_pecas"), item.get("total_pecas_liquido"),
                    item.get("total_pecas_custo"), item.get("total_pecas_lucro"),
                    item.get("total_servicos_bruto"), item.get("total_desconto_servicos"), item.get("total_servicos_liquido"),
                    item.get("total_servicos_custo"), item.get("total_servicos_lucro"), item.get("total_geral"),
                    item.get("codigo_condicao_pagamento"), item.get("descricao_condicao_pagamento"),
                    agora,
                ),
            )

            cursor.execute("DELETE FROM pos_venda_peca_raw WHERE tenant_id=%s AND codposv=%s", (tenant_id, codigo_origem))
            cursor.execute("DELETE FROM pos_venda_servico_raw WHERE tenant_id=%s AND codposv=%s", (tenant_id, codigo_origem))
            cursor.execute("DELETE FROM pos_venda_nota_raw WHERE tenant_id=%s AND codposv=%s", (tenant_id, codigo_origem))
            cursor.execute("DELETE FROM pos_venda_parcela_raw WHERE tenant_id=%s AND codposv=%s", (tenant_id, codigo_origem))

            pecas = item.get("pecas") or []
            if pecas:
                cursor.executemany(
                    """
                    INSERT INTO pos_venda_peca_raw (
                        tenant_id, codposv, codigo_peca, referencia_peca, descricao_peca, unidade_peca,
                        qtd_peca, valor_unitario, custo_unitario, custo_total, total_bruto, valor_desconto,
                        total_liquido, codigo_mecanico, nome_mecanico, percentual_comissao_mecanico,
                        valor_comissao_mecanico, peca_cancelada, codigo_motivo_cancelamento, descricao_motivo_cancelamento
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    [
                        (
                            tenant_id, codigo_origem, p.get("codigo_peca"), p.get("referencia_peca"), p.get("descricao_peca"),
                            p.get("unidade_peca"), p.get("qtd_peca"), p.get("valor_unitario"), p.get("custo_unitario"),
                            p.get("custo_total"), p.get("total_bruto"), p.get("valor_desconto"), p.get("total_liquido"),
                            p.get("codigo_mecanico"), p.get("nome_mecanico"), p.get("percentual_comissao_mecanico"),
                            p.get("valor_comissao_mecanico"), p.get("peca_cancelada"), p.get("codigo_motivo_cancelamento"),
                            p.get("descricao_motivo_cancelamento"),
                        )
                        for p in pecas
                    ],
                )

            servicos = item.get("servicos") or []
            if servicos:
                cursor.executemany(
                    """
                    INSERT INTO pos_venda_servico_raw (
                        tenant_id, codposv, codigo_servico, referencia_servico, descricao_servico, unidade_servico,
                        qtd_servico, valor_unitario, custo_unitario, custo_total, total_bruto, valor_desconto,
                        total_liquido, codigo_mecanico, nome_mecanico, percentual_comissao_mecanico,
                        valor_comissao_mecanico, servico_cancelado, codigo_motivo_cancelamento, descricao_motivo_cancelamento
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    [
                        (
                            tenant_id, codigo_origem, s.get("codigo_servico"), s.get("referencia_servico"), s.get("descricao_servico"),
                            s.get("unidade_servico"), s.get("qtd_servico"), s.get("valor_unitario"), s.get("custo_unitario"),
                            s.get("custo_total"), s.get("total_bruto"), s.get("valor_desconto"), s.get("total_liquido"),
                            s.get("codigo_mecanico"), s.get("nome_mecanico"), s.get("percentual_comissao_mecanico"),
                            s.get("valor_comissao_mecanico"), s.get("servico_cancelado"), s.get("codigo_motivo_cancelamento"),
                            s.get("descricao_motivo_cancelamento"),
                        )
                        for s in servicos
                    ],
                )

            notas = item.get("notas") or []
            if notas:
                cursor.executemany(
                    """
                    INSERT INTO pos_venda_nota_raw (
                        tenant_id, codposv, tipo, descricao, codigo_nota, numero_nota,
                        chave_nota, data_faturamento, operacao
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    [
                        (
                            tenant_id, codigo_origem, n.get("tipo"), n.get("descricao"), n.get("codigo_nota"),
                            n.get("numero_nota"), n.get("chave_nota"), _converter_data_iso(n.get("data_faturamento")),
                            n.get("operacao"),
                        )
                        for n in notas
                    ],
                )

            parcelas = (
                [(p, "PECA") for p in (item.get("parcelas_condicao_pagamento_pecas") or [])]
                + [(p, "SERVICO") for p in (item.get("parcelas_condicao_pagamento_servico") or [])]
                + [(p, "FRANQUIA") for p in (item.get("parcelas_condicao_pagamento_franquia") or [])]
            )
            if parcelas:
                cursor.executemany(
                    """
                    INSERT INTO pos_venda_parcela_raw (
                        tenant_id, codposv, tipo_parcela, ordem_parcela, vencimento_parcela,
                        forma_cobranca_parcela, valor_parcela
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    [
                        (
                            tenant_id, codigo_origem, tipo_parcela, p.get("ordem_parcela"),
                            _converter_data_br(p.get("vencimento_parcela")), p.get("forma_cobranca_parcela"),
                            p.get("valor_parcela"),
                        )
                        for p, tipo_parcela in parcelas
                    ],
                )

        conn.commit()
        # logger.info(f"[pos_venda] tenant={tenant_id} página={offset_pagina}: {len(codigos_origem)} pós-vendas persistidos.")

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ==========================================
# LEITURA PARA A SILVER
# ==========================================

def buscar_pos_venda_pendentes(tenant_id: int, limite: int = 500) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM pos_venda_raw
        WHERE tenant_id = %s AND processado_em IS NULL
        ORDER BY id
        LIMIT %s
        """,
        (tenant_id, limite),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def buscar_filhos(tabela: str, tenant_id: int, codigo_origem: int) -> list[dict]:
    if tabela not in {
        "pos_venda_peca_raw", "pos_venda_servico_raw",
        "pos_venda_nota_raw", "pos_venda_parcela_raw",
    }:
        raise ValueError(f"Tabela não reconhecida: {tabela}")
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        f"SELECT * FROM {tabela} WHERE tenant_id=%s AND codposv=%s",
        (tenant_id, codigo_origem),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def marcar_processado(ids: list[int]) -> None:
    if not ids:
        return
    conn = connection_mysql()
    cursor = conn.cursor()
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"UPDATE pos_venda_raw SET processado_em = NOW() WHERE id IN ({placeholders})",
        tuple(ids),
    )
    conn.commit()
    cursor.close()
    conn.close()


# ==========================================
# SILVER — upsert nas tabelas BI (pai + filhos)
# ==========================================

def upsert_pos_venda_bi(tenant_id: int, codigo_origem: int, bi: dict, filhos: dict) -> None:
    """
    filhos = {"pecas": [...], "servicos": [...], "notas": [...], "parcelas": [...]}
    já no formato de colunas da BI (ver silver/transform/sances/pos_venda.py).
    """
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        colunas = list(bi.keys())
        placeholders = [f"%({c})s" for c in colunas]
        updates = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_origem"]
        cursor.execute(
            f"""
            INSERT INTO pos_venda_bi ({', '.join(colunas)})
            VALUES ({', '.join(placeholders)})
            ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """,
            bi,
        )

        # busca o id interno do pai pra referenciar nos filhos
        cursor.execute(
            "SELECT id FROM pos_venda_bi WHERE tenant_id=%s AND codigo_origem=%s",
            (tenant_id, codigo_origem),
        )
        codigo_posvenda = cursor.fetchone()[0]

        for tabela, chave_codigo, linhas in (
            ("pos_venda_peca_bi", "codigo_peca", filhos.get("pecas", [])),
            ("pos_venda_servico_bi", "codigo_servico", filhos.get("servicos", [])),
            ("nota_bi", "codigo_nota", filhos.get("notas", [])),
            ("pos_venda_parcela_bi", None, filhos.get("parcelas", [])),
        ):
            cursor.execute(
                f"DELETE FROM {tabela} WHERE tenant_id=%s AND codigo_origem=%s",
                (tenant_id, codigo_origem),
            )
            if not linhas:
                continue
            for linha in linhas:
                linha["tenant_id"] = tenant_id
                linha["codigo_posvenda"] = codigo_posvenda
                linha["codigo_origem"] = codigo_origem
            colunas_f = list(linhas[0].keys())
            placeholders_f = ", ".join(["%s"] * len(colunas_f))
            cursor.executemany(
                f"INSERT INTO {tabela} ({', '.join(colunas_f)}) VALUES ({placeholders_f})",
                [tuple(linha[c] for c in colunas_f) for linha in linhas],
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()