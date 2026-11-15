import json
import logging
from datetime import datetime

from database.mysql_connection import connection_mysql

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def _converter_data_iso(valor) -> datetime | None:
    """Converte datas ISO com offset ou Z para datetime."""
    if not valor:
        return None

    try:
        valor = str(valor).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def _converter_data_br(valor) -> str | None:
    """Converte DD/MM/YYYY para YYYY-MM-DD."""
    if not valor:
        return None

    try:
        return datetime.strptime(
            str(valor).strip(), "%d/%m/%Y"
        ).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _booleano_mysql(valor, padrao=0) -> int:
    """Normaliza booleanos da API para 0 ou 1."""
    if valor is None:
        return padrao

    if isinstance(valor, str):
        return 1 if valor.strip().lower() in (
            "1", "true", "sim", "s", "yes"
        ) else 0

    return 1 if valor else 0


# ============================================================
# BRONZE - TABELA PRINCIPAL
# ============================================================

CAMPOS_DIRETOS = [
    "tipo",
    "descricao_tipo",
    "numero",
    "codigo_situacao",
    "situacao",
    "codigo_empresa",
    "nome_empresa",
    "codigo_cliente",
    "nome_cliente",
    "codigo_tipo_preco",
    "descricao_tipo_preco",
    "codigo_veiculo",
    "placa_veiculo",
    "codigo_modelo_veiculo",
    "descricao_modelo_veiculo",
    "codigo_cor_veiculo",
    "descricao_cor_veiculo",
    "ano_fabricacao_veiculo",
    "ano_modelo_veiculo",
    "codigo_tipo_os",
    "descricao_tipo_os",
    "km_entrada",
    "km_saida",
    "solicitacao_cliente",
    "avaria",
    "defeito_averiguado",
    "codigo_proprietario",
    "nome_proprietario",
    "codigo_tipo_midia",
    "descricao_tipo_midia",
    "codigo_modalidade_venda",
    "descricao_modalidade_venda",
    "codigo_conveniado",
    "nome_conveniado",
    "codigo_consultor",
    "nome_consultor",
    "percentual_comissao_peca",
    "valor_comissao_peca_consultor",
    "percentual_comissao_servico",
    "valor_comissao_servico_consultor",
    "total_comissao_consultor",
    "observacao",
    "observacao_nota",
    "codigo_usuario_insercao",
    "nome_usuario_insercao",
    "codigo_usuario_alteracao",
    "nome_usuario_alteracao",
    "codigo_usuario_cancelamento",
    "nome_usuario_cancelamento",
    "codigo_usuario_fechamento",
    "nome_usuario_fechamento",
    "valor_seguro",
    "valor_frete",
    "valor_despesas",
    "valor_acrescimo_financeiro",
    "total_pecas_bruto",
    "total_desconto_pecas",
    "total_pecas_liquido",
    "total_pecas_custo",
    "total_pecas_lucro",
    "total_servicos_bruto",
    "total_desconto_servicos",
    "total_servicos_liquido",
    "total_servicos_custo",
    "total_servicos_lucro",
    "total_geral",
    "codigo_condicao_pagamento",
    "descricao_condicao_pagamento",
]

CAMPOS_BOOLEANOS = [
    "orcamento_os",
    "aguardando_liberacao",
]

CAMPOS_DATA_ISO = [
    "data_entrada",
    "data_saida",
    "data_insercao",
    "data_alteracao",
    "data_cancelamento",
    "data_fechamento",
]


def _linha_pos_venda_raw(
    tenant_id: int,
    codigo,
    item: dict,
    agora: datetime,
) -> dict:

    linha = {
        "tenant_id": tenant_id,
        "codigo": codigo,
        "atualizado_em": agora,
    }

    for campo in CAMPOS_DIRETOS:
        linha[campo] = item.get(campo)

    for campo in CAMPOS_BOOLEANOS:
        linha[campo] = _booleano_mysql(item.get(campo))

    for campo in CAMPOS_DATA_ISO:
        linha[campo] = _converter_data_iso(item.get(campo))

    return linha


def _upsert_principal(cursor, dados: dict) -> None:
    colunas = list(dados.keys())

    colunas_sql = ", ".join(f"`{c}`" for c in colunas)
    placeholders = ", ".join(["%s"] * len(colunas))

    updates = [
        f"`{c}`=VALUES(`{c}`)"
        for c in colunas
        if c not in ("tenant_id", "codigo")
    ]

    sql = f"""
        INSERT INTO `pos_venda_raw` ({colunas_sql})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
            `processado_em` = IF(
                `processado_em`,
                NULL
            ),
            {", ".join(updates)},
    """

    cursor.execute(sql, tuple(dados.values()))


# ============================================================
# BRONZE - TABELAS FILHAS
# ============================================================

CAMPOS_PECA = [
    "codigo_peca",
    "referencia_peca",
    "descricao_peca",
    "unidade_peca",
    "qtd_peca",
    "valor_unitario",
    "custo_unitario",
    "custo_total",
    "total_bruto",
    "valor_desconto",
    "total_liquido",
    "codigo_mecanico",
    "nome_mecanico",
    "percentual_comissao_mecanico",
    "valor_comissao_mecanico",
    "peca_cancelada",
    "codigo_motivo_cancelamento",
    "descricao_motivo_cancelamento",
]

CAMPOS_SERVICO = [
    "codigo_servico",
    "referencia_servico",
    "descricao_servico",
    "unidade_servico",
    "qtd_servico",
    "valor_unitario",
    "custo_unitario",
    "custo_total",
    "total_bruto",
    "valor_desconto",
    "total_liquido",
    "codigo_mecanico",
    "nome_mecanico",
    "percentual_comissao_mecanico",
    "valor_comissao_mecanico",
    "servico_cancelado",
    "codigo_motivo_cancelamento",
    "descricao_motivo_cancelamento",
]

CAMPOS_NOTA = [
    "tipo",
    "descricao",
    "codigo_nota",
    "numero_nota",
    "chave_nota",
    "data_faturamento",
    "operacao",
]

CAMPOS_PARCELA = [
    "tipo_parcela",
    "ordem_parcela",
    "vencimento_parcela",
    "forma_cobranca_parcela",
    "valor_parcela",
]

TABELAS_FILHAS_RAW = (
    "pos_venda_peca_raw",
    "pos_venda_servico_raw",
    "pos_venda_nota_raw",
    "pos_venda_parcela_raw",
)


def _inserir_filhos(
    cursor,
    tabela: str,
    tenant_id: int,
    codigo_origem,
    campos: list[str],
    linhas: list[dict],
    booleanos: tuple = (),
    datas_iso: tuple = (),
    datas_br: tuple = (),
) -> None:
    """
    UPSERT incremental dos filhos pela chave (tenant_id, codposv, tipo).
    Não apaga nada: linhas existentes são atualizadas no lugar.
    """

    if not linhas:
        return

    colunas = ["tenant_id", "codigo", "codposv", *campos]

    colunas_sql = ", ".join(f"`{c}`" for c in colunas)
    placeholders = ", ".join(["%s"] * len(colunas))
    updates = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in campos)

    sql = f"""
        INSERT INTO `{tabela}` ({colunas_sql})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
    """

    def normalizar_valor(linha: dict, campo: str):
        valor = linha.get(campo)

        if campo in booleanos:
            return _booleano_mysql(valor)

        if campo in datas_iso:
            return _converter_data_iso(valor)

        if campo in datas_br:
            return _converter_data_br(valor)

        return valor

    valores = [
        (
            tenant_id,
            codigo_origem,
            codigo_origem,
            *[normalizar_valor(linha, campo) for campo in campos],
        )
        for linha in enumerate(linhas)
    ]

    cursor.executemany(sql, valores)


def _montar_parcelas(item: dict) -> list[dict]:
    parcelas = []

    for chave, tipo in (
        ("parcelas_condicao_pagamento_pecas", "PECA"),
        ("parcelas_condicao_pagamento_servico", "SERVICO"),
        ("parcelas_condicao_pagamento_franquia", "FRANQUIA"),
    ):
        for p in item.get(chave) or []:
            parcelas.append({**p, "tipo_parcela": tipo})

    return parcelas


def _salvar_filhos_item(cursor, tenant_id: int, codigo_origem, item: dict) -> None:

    _inserir_filhos(
        cursor, "pos_venda_peca_raw", tenant_id, codigo_origem,
        CAMPOS_PECA, item.get("pecas") or [],
        booleanos=("peca_cancelada",),
    )

    _inserir_filhos(
        cursor, "pos_venda_servico_raw", tenant_id, codigo_origem,
        CAMPOS_SERVICO, item.get("servicos") or [],
        booleanos=("servico_cancelado",),
    )

    _inserir_filhos(
        cursor, "pos_venda_nota_raw", tenant_id, codigo_origem,
        CAMPOS_NOTA, item.get("notas") or [],
        datas_iso=("data_faturamento",),
    )

    _inserir_filhos(
        cursor, "pos_venda_parcela_raw", tenant_id, codigo_origem,
        CAMPOS_PARCELA, _montar_parcelas(item),
        datas_br=("vencimento_parcela",),
    )


# ============================================================
# BRONZE - SALVAR PÁGINA (INCREMENTAL)
# ============================================================

def salvar_pagina_raw(
    tenant_id: int,
    pipeline: str,
    offset_pagina: int,
    itens: list[dict],
) -> None:

    if not itens:
        return

    invalidos = [i for i in itens if not isinstance(i, dict)]
    if invalidos:
        logger.error(
            "Itens inválidos ignorados: tenant=%s offset=%s qtd=%s exemplo=%r",
            tenant_id, offset_pagina, len(invalidos), invalidos[0],
        )
        itens = [i for i in itens if isinstance(i, dict)]
        if not itens:
            return

    agora = datetime.now()

    conn = connection_mysql()
    cursor = conn.cursor()

    try:

        codigos = [
            i.get("codigo") for i in itens
            if i.get("codigo") is not None
        ]

        gravados = 0
        ignorados = 0

        for item in itens:

            codigo_origem = item.get("codigo")

            if codigo_origem is None:
                logger.warning(
                    "Pós-venda sem código ignorada: tenant=%s offset=%s",
                    tenant_id,
                    offset_pagina,
                )
                continue

            dados = _linha_pos_venda_raw(
                tenant_id,
                codigo_origem,
                item,
                agora,
            )

            _upsert_principal(cursor, dados)
            _salvar_filhos_item(cursor, tenant_id, codigo_origem, item)

            gravados += 1

        conn.commit()

        logger.info(
            "Pós-vendas bronze: tenant=%s pipeline=%s offset=%s "
            "gravados=%s ignorados=%s",
            tenant_id,
            pipeline,
            offset_pagina,
            gravados,
            ignorados,
        )

    except Exception:

        conn.rollback()

        logger.exception(
            "Erro ao salvar pós-vendas: tenant=%s pipeline=%s offset=%s",
            tenant_id,
            pipeline,
            offset_pagina,
        )

        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# LEITURA PARA SILVER
# ============================================================

def buscar_pos_venda_pendentes(
    tenant_id: int,
    limite: int = 500,
    ultimo_id: int = 0,
) -> list[dict]:
    """
    Busca pendentes (processado_em IS NULL) usando paginação por id (keyset).
    O ultimo_id impede que registros com erro sejam relidos em loop
    e bloqueiem a fila.
    """

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT *
            FROM pos_venda_raw
            WHERE tenant_id = %s
              AND processado_em IS NULL
              AND id > %s
            ORDER BY id
            LIMIT %s
            """,
            (tenant_id, ultimo_id, limite),
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def contar_pos_venda_pendentes(tenant_id: int) -> int:
    """Quantos registros ainda estão com processado_em NULL (acompanhamento)."""

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM pos_venda_raw
            WHERE tenant_id = %s
              AND processado_em IS NULL
            """,
            (tenant_id,),
        )

        return cursor.fetchone()[0]

    finally:
        cursor.close()
        conn.close()

        
def buscar_filhos_lote(
    tenant_id: int,
    codigo: int,
    tabela: str,
    limite: int = 200,
) -> list[dict]:
    """
    Busca um lote de filhos de um único pós-venda.

    Não carrega todos os filhos na memória.
    """

    tabelas_permitidas = {
        "pos_venda_peca_raw",
        "pos_venda_servico_raw",
        "pos_venda_nota_raw",
        "pos_venda_parcela_raw",
    }

    if tabela not in tabelas_permitidas:
        raise ValueError(f"Tabela de filhos não permitida: {tabela}")

    limite = max(1, min(int(limite), 200))

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
                SELECT *
                FROM `{tabela}`
                WHERE tenant_id = %s
                  AND codposv = %s
                LIMIT %s
            """,
            (tenant_id, codigo, limite),
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()
        
def marcar_processado(
    tenant_id: int,
    registros: list[int],
) -> None:
    """
    Marca individualmente os registros processados na Silver.
    """
    if not registros:
        return

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            """
            UPDATE pos_venda_raw
            SET processado_em = NOW()
            WHERE tenant_id = %s
              AND id = %s
              AND processado_em IS NULL
            """,
            [
                (tenant_id, registro_id)
                for registro_id in registros
            ],
        )

        conn.commit()

    except Exception:
        conn.rollback()
        logger.exception(
            "Erro ao marcar pós-venda processado: tenant=%s",
            tenant_id,
        )
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# SILVER - COLUNAS DAS TABELAS BI FILHAS
# ============================================================

COLUNAS_BI_FILHOS = {

    "pos_venda_peca_bi": [
        "codigo_peca",
        "unidade_peca",
        "qtd_peca",
        "valor_unitario",
        "custo_unitario",
        "custo_total",
        "total_bruto",
        "valor_desconto",
        "total_liquido",
        "codigo_mecanico",
        "percentual_comissao_mecanico",
        "valor_comissao_mecanico",
        "peca_cancelada",
        "codigo_motivo_cancelamento",
    ],

    "pos_venda_servico_bi": [
        "codigo_servico",
        "referencia_servico",
        "descricao_servico",
        "unidade_servico",
        "qtd_servico",
        "valor_unitario",
        "custo_unitario",
        "custo_total",
        "total_bruto",
        "valor_desconto",
        "total_liquido",
        "codigo_mecanico",
        "nome_mecanico",
        "percentual_comissao_mecanico",
        "valor_comissao_mecanico",
        "servico_cancelado",
        "codigo_motivo_cancelamento",
    ],

    "nota_bi": [
        "tipo",
        "descricao",
        "codigo_nota",
        "numero_nota",
        "chave_nota",
        "data_faturamento",
        "operacao",
    ],

    "pos_venda_parcela_bi": [
        "tipo_parcela",
        "ordem_parcela",
        "vencimento_parcela",
        "forma_cobranca_parcela",
        "valor_parcela",
    ],
}


# ============================================================
# SILVER - UPSERT DO PÓS-VENDA (INCREMENTAL)
# ============================================================

def upsert_pos_venda_bi_principal(
    tenant_id: int,
    codigo_origem: int,
    bi: dict,
) -> None:

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        bi = dict(bi)

        bi["tenant_id"] = tenant_id
        bi["codigo"] = codigo_origem
        bi["codigo_origem"] = codigo_origem

        colunas = list(bi.keys())

        placeholders = [f"%({c})s" for c in colunas]

        updates = [
            f"`{c}`=VALUES(`{c}`)"
            for c in colunas
            if c not in (
                "tenant_id",
                "codigo",
                "codigo_origem",
            )
        ]

        sql = f"""
            INSERT INTO pos_venda_bi ({", ".join(f"`{c}`" for c in colunas)})
            VALUES ({", ".join(placeholders)})
            ON DUPLICATE KEY UPDATE
                {", ".join(updates)}
        """

        cursor.execute(sql, bi)

        conn.commit()

    except Exception:
        conn.rollback()
        logger.exception(
            "Erro ao gravar principal: tenant=%s codigo=%s",
            tenant_id,
            codigo_origem,
        )
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# SILVER - UPSERT DO FILHOS (INCREMENTAL)
# ============================================================

def upsert_pos_venda_bi_filhos(
    tenant_id: int,
    codigo_origem: int,
    tabela: str,
    linhas: list[dict],
) -> None:

    if not linhas:
        return

    if tabela not in COLUNAS_BI_FILHOS:
        raise ValueError(f"Tabela BI não permitida: {tabela}")

    campos = COLUNAS_BI_FILHOS[tabela]

    colunas = [
        "tenant_id",
        "codigo",
        "codigo_posvenda",
        "codigo_origem",
        *campos,
        "data_carga",
    ]

    colunas_sql = ", ".join(f"`{c}`" for c in colunas)
    placeholders = ", ".join(["%s"] * len(colunas))

    updates = ", ".join(
        f"`{c}`=VALUES(`{c}`)"
        for c in (*campos, "data_carga")
    )

    sql = f"""
        INSERT INTO `{tabela}` ({colunas_sql})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates}
    """

    agora = datetime.now()

    valores = [
        (
            tenant_id,
            codigo_origem,
            codigo_origem,
            codigo_origem,
            *[linha.get(campo) for campo in campos],
            agora,
        )
        for linha in linhas
    ]

    conn = connection_mysql()
    cursor = conn.cursor()

    try:
        cursor.executemany(sql, valores)
        conn.commit()

    except Exception:
        conn.rollback()
        logger.exception(
            "Erro ao gravar filhos: tenant=%s codigo=%s tabela=%s",
            tenant_id,
            codigo_origem,
            tabela,
        )
        raise

    finally:
        cursor.close()
        conn.close()