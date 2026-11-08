import logging
from datetime import datetime
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


# ── Helper: INSERT ... ON DUPLICATE KEY UPDATE montado a partir das colunas ──
# Colunas e valores saem da MESMA lista, então os placeholders nunca
# ficam fora de sincronia com as tuplas.

def _upsert_lote(
    cursor,
    tabela: str,
    colunas: list[str],
    chaves: tuple,
    linhas: list[dict],
) -> None:
    """
    chaves: colunas que identificam o registro (unique key) e, por isso,
            não entram no UPDATE.
    """
    if not linhas:
        return

    colunas_sql = ", ".join(f"`{c}`" for c in colunas)
    placeholders = ", ".join(["%s"] * len(colunas))

    updates = [
        f"`{c}` = VALUES(`{c}`)"
        for c in colunas
        if c not in chaves
    ]
    updates.append("`processado_em` = NULL")

    sql = f"""
        INSERT INTO `{tabela}` ({colunas_sql})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
            {", ".join(updates)}
    """

    valores = [tuple(linha[c] for c in colunas) for linha in linhas]
    cursor.executemany(sql, valores)


COLUNAS_PRODUTO = [
    "tenant_id", "offset_pagina",
    "codigo", "descricao", "referencia", "referencia_fabrica",
    "endereco_setor", "endereco_rua", "endereco_andar",
    "sigla_unidade_medida", "descricao_unidade_medida",
    "codigo_categoria", "descricao_categoria",
    "descricao_grupo", "descricao_subgrupo",
    "codigo_ean", "codigo_barras", "ativo", "data_extracao",
]

COLUNAS_PRECO = [
    "tenant_id", "offset_pagina",
    "codigo_produto", "codigo_empresa", "cnpj", "nome_razao",
    "nome_fantasia", "apelido",
    "custo_medio", "venda_varejo", "venda_atacado", "venda_ecommerce",
    "garantia", "sugerido", "reposicao", "promocao",
    "personalizado1", "personalizado3", "data_extracao",
]

COLUNAS_QUANTIDADE = [
    "tenant_id", "offset_pagina",
    "codigo_produto", "codigo_empresa", "cnpj", "nome_razao",
    "nome_fantasia", "apelido",
    "qtd_estoque", "qtd_aplicadas", "qtd_reservada",
    "qtd_transito", "qtd_pedido", "qtd_bo", "data_extracao",
]

COLUNAS_MODELO = [
    "tenant_id", "offset_pagina",
    "codigo_produto", "codigo_modelo", "descricao_modelo", "data_extracao",
]


def salvar_pagina_raw(
    tenant_id: int,
    offset_pagina: int,
    itens: list[dict],
) -> None:
    """
    Grava nas 4 tabelas Bronze
    """
    if not itens:
        return

    agora = datetime.now()
    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        linhas_produto = []
        linhas_preco = []
        linhas_quantidade = []
        linhas_modelo = []

        base = {
            "tenant_id": tenant_id,
            "offset_pagina": offset_pagina,
            "data_extracao": agora,
        }

        for item in itens:
            codigo = item.get("codigo")

            ref_fabrica = item.get("referenciaFabrica")
            ref_fabrica_str = (
                ";".join(str(r) for r in ref_fabrica if r) if ref_fabrica else None
            )

            linhas_produto.append({
                **base,
                "codigo": codigo,
                "descricao": item.get("descricao"),
                "referencia": item.get("referencia"),
                "referencia_fabrica": ref_fabrica_str,
                "endereco_setor": item.get("endereco_setor"),
                "endereco_rua": item.get("endereco_rua"),
                "endereco_andar": item.get("endereco_andar"),
                "sigla_unidade_medida": item.get("siglaUnidadeMedida"),
                "descricao_unidade_medida": item.get("descricaoUnidadeMedida"),
                "codigo_categoria": item.get("codigoCategoria"),
                "descricao_categoria": item.get("descricaoCategoria"),
                "descricao_grupo": item.get("descricaoGrupo"),
                "descricao_subgrupo": item.get("descricaoSubGrupo"),
                "codigo_ean": item.get("codigoEAN"),
                "codigo_barras": item.get("codigoBarras"),
                "ativo": item.get("ativo"),
            })

            for p in (item.get("precos") or []):
                linhas_preco.append({
                    **base,
                    "codigo_produto": codigo,
                    "codigo_empresa": p.get("codigoEmpresa"),
                    "cnpj": p.get("cnpj"),
                    "nome_razao": p.get("nomeRazao"),
                    "nome_fantasia": p.get("nomeFantasia"),
                    "apelido": p.get("apelido"),
                    "custo_medio": p.get("custoMedio"),
                    "venda_varejo": p.get("vendaVarejo"),
                    "venda_atacado": p.get("vendaAtacado"),
                    "venda_ecommerce": p.get("vendaEcommerce"),
                    "garantia": p.get("garantia"),
                    "sugerido": p.get("sugerido"),
                    "reposicao": p.get("reposicao"),
                    "promocao": p.get("promocao"),
                    "personalizado1": p.get("personalizado1"),
                    "personalizado3": p.get("personalizado3"),
                })

            for e in (item.get("estoque") or []):
                linhas_quantidade.append({
                    **base,
                    "codigo_produto": codigo,
                    "codigo_empresa": e.get("codigoEmpresa"),
                    "cnpj": e.get("cnpj"),
                    "nome_razao": e.get("nomeRazao"),
                    "nome_fantasia": e.get("nomeFantasia"),
                    "apelido": e.get("apelido"),
                    "qtd_estoque": e.get("qtdEstoque"),
                    "qtd_aplicadas": e.get("qtdAplicadas"),
                    "qtd_reservada": e.get("qtdReservada"),
                    "qtd_transito": e.get("qtdTransito"),
                    "qtd_pedido": e.get("qtdPedido"),
                    "qtd_bo": e.get("qtdBO"),
                })

            for m in (item.get("modeloVeiculo") or []):
                if not m.get("codigoModelo"):
                    continue
                linhas_modelo.append({
                    **base,
                    "codigo_produto": codigo,
                    "codigo_modelo": m.get("codigoModelo"),
                    "descricao_modelo": m.get("descricaoModelo"),
                })

        _upsert_lote(
            cursor, "produto_sances_raw", COLUNAS_PRODUTO,
            chaves=("tenant_id", "codigo"),
            linhas=linhas_produto,
        )

        _upsert_lote(
            cursor, "preco_sances_raw", COLUNAS_PRECO,
            chaves=("tenant_id", "codigo_produto", "codigo_empresa"),
            linhas=linhas_preco,
        )

        _upsert_lote(
            cursor, "quantidade_sances_raw", COLUNAS_QUANTIDADE,
            chaves=("tenant_id", "codigo_produto", "codigo_empresa"),
            linhas=linhas_quantidade,
        )

        _upsert_lote(
            cursor, "modelo_veiculo_sances_raw", COLUNAS_MODELO,
            chaves=("tenant_id", "codigo_produto", "codigo_modelo"),
            linhas=linhas_modelo,
        )

        conn.commit()

    except Exception:
        conn.rollback()
        logger.exception(
            "Erro ao salvar estoque: tenant=%s offset=%s",
            tenant_id, offset_pagina,
        )
        raise
    finally:
        cursor.close()
        conn.close()


# ── Leitura para a Silver ────────────────────────────────────

def buscar_produtos_pendentes(tenant_id: int, limite: int = 500) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT *
        FROM produto_sances_raw
        WHERE tenant_id = %s
        AND processado_em IS NULL
        ORDER BY id
        LIMIT %s
        """,
        (tenant_id, limite),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def buscar_precos_do_produto(tenant_id: int, codigo_produto: int) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM preco_sances_raw WHERE tenant_id = %s AND codigo_produto = %s ORDER BY id DESC",
        (tenant_id, codigo_produto),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def buscar_quantidade_do_produto(tenant_id: int, codigo_produto: int) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM quantidade_sances_raw WHERE tenant_id = %s AND codigo_produto = %s ORDER BY id DESC",
        (tenant_id, codigo_produto),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def buscar_modelos_do_produto(tenant_id: int, codigo_produto: int) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM modelo_veiculo_sances_raw WHERE tenant_id = %s AND codigo_produto = %s ORDER BY id DESC",
        (tenant_id, codigo_produto),
    )
    linhas = cursor.fetchall()
    cursor.close()
    conn.close()
    return linhas


def marcar_processado(tabela: str, ids: list[int]) -> None:
    """Marca processado_em=NOW() para os ids informados na tabela Bronze indicada."""
    if not ids:
        return
    if tabela not in {
        "produto_sances_raw", "preco_sances_raw",
        "quantidade_sances_raw", "modelo_veiculo_sances_raw",
    }:
        raise ValueError(f"Tabela não reconhecida: {tabela}")

    conn = connection_mysql()
    cursor = conn.cursor()
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"UPDATE {tabela} SET processado_em = NOW() WHERE id IN ({placeholders})",
        tuple(ids),
    )
    conn.commit()
    cursor.close()
    conn.close()