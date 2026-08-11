import logging
from datetime import datetime
from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


def salvar_pagina_raw(
    tenant_id: int,
    pipeline: str,
    offset_pagina: int,
    itens: list[dict],
) -> None:
    """
    Grava uma página inteira nas 4 tabelas Bronze (append-only, sem
    upsert). Cada `item` é um produto com os blocos aninhados originais
    da API (referenciaFabrica, precos, estoque, modeloVeiculo).

    Levanta exceção se qualquer INSERT falhar — quem chama (bronze/extract/
    sances/estoque.py) depende disso pra NÃO avançar o offset em caso de
    falha na gravação.
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

        for item in itens:
            codigo = item.get("codigo")

            ref_fabrica = item.get("referenciaFabrica")
            ref_fabrica_str = ";".join(str(r) for r in ref_fabrica if r) if ref_fabrica else None

            linhas_produto.append((
                tenant_id, pipeline, offset_pagina,
                codigo, item.get("descricao"), item.get("referencia"), ref_fabrica_str,
                item.get("endereco_setor"), item.get("endereco_rua"), item.get("endereco_andar"),
                item.get("siglaUnidadeMedida"), item.get("descricaoUnidadeMedida"),
                item.get("codigoCategoria"), item.get("descricaoCategoria"),
                item.get("descricaoGrupo"), item.get("descricaoSubGrupo"),
                item.get("codigoEAN"), item.get("codigoBarras"), item.get("ativo"),
                agora,
            ))

            for p in (item.get("precos") or []):
                linhas_preco.append((
                    tenant_id, pipeline, offset_pagina,
                    codigo, p.get("codigoEmpresa"), p.get("cnpj"), p.get("nomeRazao"),
                    p.get("nomeFantasia"), p.get("apelido"),
                    p.get("custoMedio"), p.get("vendaVarejo"), p.get("vendaAtacado"), p.get("vendaEcommerce"),
                    p.get("garantia"), p.get("sugerido"), p.get("reposicao"), p.get("promocao"),
                    p.get("personalizado1"), p.get("personalizado3"),
                    agora,
                ))

            for e in (item.get("estoque") or []):
                linhas_quantidade.append((
                    tenant_id, pipeline, offset_pagina,
                    codigo, e.get("codigoEmpresa"), e.get("cnpj"), e.get("nomeRazao"),
                    e.get("nomeFantasia"), e.get("apelido"),
                    e.get("qtdEstoque"), e.get("qtdAplicadas"), e.get("qtdReservada"),
                    e.get("qtdTransito"), e.get("qtdPedido"), e.get("qtdBO"),
                    agora,
                ))

            for m in (item.get("modeloVeiculo") or []):
                if not m.get("codigoModelo"):
                    continue  # descarta o sentinela {"codigoModelo": 0, "descricaoModelo": ""}
                linhas_modelo.append((
                    tenant_id, pipeline, offset_pagina,
                    codigo, m.get("codigoModelo"), m.get("descricaoModelo"),
                    agora,
                ))

        if linhas_produto:
            cursor.executemany(
                """
                INSERT INTO produto_sances_raw
                    (tenant_id, pipeline, offset_pagina, codigo, descricao, referencia, referencia_fabrica,
                     endereco_setor, endereco_rua, endereco_andar, sigla_unidade_medida, descricao_unidade_medida,
                     codigo_categoria, descricao_categoria, descricao_grupo, descricao_subgrupo,
                     codigo_ean, codigo_barras, ativo, data_extracao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                linhas_produto,
            )

        if linhas_preco:
            cursor.executemany(
                """
                INSERT INTO preco_sances_raw
                    (tenant_id, pipeline, offset_pagina, codigo_produto, codigo_empresa, cnpj, nome_razao,
                     nome_fantasia, apelido, custo_medio, venda_varejo, venda_atacado, venda_ecommerce,
                     garantia, sugerido, reposicao, promocao, personalizado1, personalizado3, data_extracao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                linhas_preco,
            )

        if linhas_quantidade:
            cursor.executemany(
                """
                INSERT INTO quantidade_sances_raw
                    (tenant_id, pipeline, offset_pagina, codigo_produto, codigo_empresa, cnpj, nome_razao,
                     nome_fantasia, apelido, qtd_estoque, qtd_aplicadas, qtd_reservada,
                     qtd_transito, qtd_pedido, qtd_bo, data_extracao)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                linhas_quantidade,
            )

        if linhas_modelo:
            cursor.executemany(
                """
                INSERT INTO modelo_veiculo_sances_raw
                    (tenant_id, pipeline, offset_pagina, codigo_produto, codigo_modelo, descricao_modelo, data_extracao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                linhas_modelo,
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ── Leitura para a Silver ────────────────────────────────────

def buscar_produtos_pendentes(tenant_id: int, pipeline: str, limite: int = 500) -> list[dict]:
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT * FROM produto_sances_raw
        WHERE tenant_id = %s AND pipeline = %s AND processado_em IS NULL
        ORDER BY id
        LIMIT %s
        """,
        (tenant_id, pipeline, limite),
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
