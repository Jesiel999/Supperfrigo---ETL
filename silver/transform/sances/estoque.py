import json
import logging
from datetime import datetime
from database.mysql_connection import connection_mysql

from repositories.sances.estoque_repository import (
    buscar_produtos_pendentes,
    buscar_precos_do_produto,
    buscar_quantidade_do_produto,
    buscar_modelos_do_produto,
    marcar_processado,
)

logger = logging.getLogger(__name__)


def _upsert_produto(tenant_id: int, codigo_produto: int, p: dict, agora: datetime) -> None:
    ref_fabrica_json = (
        json.dumps(p["referencia_fabrica"].split(";")) if p.get("referencia_fabrica") else None
    )

    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estoque_produto_bi
            (tenant_id, codigo_produto, descricao, referencia, referencia_fabrica, codigo_ean, codigo_barras,
             sigla_unidade_medida, descricao_unidade_medida, codigo_categoria, descricao_categoria,
             descricao_grupo, descricao_subgrupo, endereco_setor, endereco_rua, endereco_andar, ativo,
             data_processamento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            descricao = VALUES(descricao),
            referencia = VALUES(referencia),
            referencia_fabrica = VALUES(referencia_fabrica),
            codigo_ean = VALUES(codigo_ean),
            codigo_barras = VALUES(codigo_barras),
            sigla_unidade_medida = VALUES(sigla_unidade_medida),
            descricao_unidade_medida = VALUES(descricao_unidade_medida),
            codigo_categoria = VALUES(codigo_categoria),
            descricao_categoria = VALUES(descricao_categoria),
            descricao_grupo = VALUES(descricao_grupo),
            descricao_subgrupo = VALUES(descricao_subgrupo),
            endereco_setor = VALUES(endereco_setor),
            endereco_rua = VALUES(endereco_rua),
            endereco_andar = VALUES(endereco_andar),
            ativo = VALUES(ativo),
            data_processamento = VALUES(data_processamento)
        """,
        (
            tenant_id, codigo_produto, p.get("descricao"), p.get("referencia"), ref_fabrica_json,
            p.get("codigo_ean"), p.get("codigo_barras"),
            p.get("sigla_unidade_medida"), p.get("descricao_unidade_medida"),
            p.get("codigo_categoria"), p.get("descricao_categoria"),
            p.get("descricao_grupo"), p.get("descricao_subgrupo"),
            p.get("endereco_setor"), p.get("endereco_rua"), p.get("endereco_andar"),
            p.get("ativo"), agora,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _upsert_preco(tenant_id: int, codigo_produto: int, pr: dict, agora: datetime) -> None:
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estoque_precos_bi
            (tenant_id, codigo_produto, codigo_empresa, cnpj, custo_medio, venda_varejo, venda_atacado,
             venda_ecommerce, garantia, sugerido, reposicao, promocao, personalizado1, personalizado3,
             data_processamento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            cnpj = VALUES(cnpj), custo_medio = VALUES(custo_medio), venda_varejo = VALUES(venda_varejo),
            venda_atacado = VALUES(venda_atacado), venda_ecommerce = VALUES(venda_ecommerce),
            garantia = VALUES(garantia), sugerido = VALUES(sugerido), reposicao = VALUES(reposicao),
            promocao = VALUES(promocao), personalizado1 = VALUES(personalizado1),
            personalizado3 = VALUES(personalizado3), data_processamento = VALUES(data_processamento)
        """,
        (
            tenant_id, codigo_produto, pr.get("codigo_empresa"), pr.get("cnpj"),
            pr.get("custo_medio"), pr.get("venda_varejo"), pr.get("venda_atacado"), pr.get("venda_ecommerce"),
            pr.get("garantia"), pr.get("sugerido"), pr.get("reposicao"), pr.get("promocao"),
            pr.get("personalizado1"), pr.get("personalizado3"), agora,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _upsert_empresa(tenant_id: int, codigo_produto: int, e: dict, agora: datetime) -> None:
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estoque_empresa_bi
            (tenant_id, codigo_produto, codigo_empresa, cnpj, nome_razao, nome_fantasia, apelido,
             qtd_estoque, qtd_aplicadas, qtd_reservada, qtd_transito, qtd_pedido, qtd_bo, data_processamento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            cnpj = VALUES(cnpj), nome_razao = VALUES(nome_razao), nome_fantasia = VALUES(nome_fantasia),
            apelido = VALUES(apelido), qtd_estoque = VALUES(qtd_estoque), qtd_aplicadas = VALUES(qtd_aplicadas),
            qtd_reservada = VALUES(qtd_reservada), qtd_transito = VALUES(qtd_transito),
            qtd_pedido = VALUES(qtd_pedido), qtd_bo = VALUES(qtd_bo), data_processamento = VALUES(data_processamento)
        """,
        (
            tenant_id, codigo_produto, e.get("codigo_empresa"), e.get("cnpj"),
            e.get("nome_razao"), e.get("nome_fantasia"), e.get("apelido"),
            e.get("qtd_estoque"), e.get("qtd_aplicadas"), e.get("qtd_reservada"),
            e.get("qtd_transito"), e.get("qtd_pedido"), e.get("qtd_bo"), agora,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _upsert_modelo(tenant_id: int, codigo_produto: int, m: dict, agora: datetime) -> None:
    conn = connection_mysql()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estoque_modelo_veiculo_bi
            (tenant_id, codigo_produto, codigo_modelo, descricao_modelo, data_processamento)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            descricao_modelo = VALUES(descricao_modelo), data_processamento = VALUES(data_processamento)
        """,
        (tenant_id, codigo_produto, m.get("codigo_modelo"), m.get("descricao_modelo"), agora),
    )
    conn.commit()
    cursor.close()
    conn.close()


def _mais_recente_por_chave(linhas: list[dict], campo_chave: str) -> dict:
    """
    Linhas vêm ORDER BY id DESC (mais recente primeiro) — mantém só a
    primeira ocorrência de cada valor de `campo_chave`, descartando o
    histórico mais antigo dessa mesma empresa/modelo.
    """
    resultado = {}
    for linha in linhas:
        chave = linha[campo_chave]
        if chave not in resultado: 
            resultado[chave] = linha
    return resultado


def processar_produtos_pendentes(
    tenant_id: int,
    pipeline: str = "estoque_sances",
    limite: int = 500,
) -> dict:
    """
    StepTransformarEstoque: lê produtos ainda não processados na Bronze,
    faz upsert em estoque_produto/estoque_empresa/estoque_precos/
    estoque_modelo_veiculo (chaves compostas com tenant_id) e marca a
    linha de produto_sances_raw como processada.

    As tabelas filhas (preco/quantidade/modelo) não têm sua própria
    marcação individual de processado — a cada produto processado, TODO
    o histórico dessas tabelas pra aquele codigo_produto é relido, e fica
    só a linha mais recente por empresa/modelo (dedup em memória). Isso é
    intencional: mantém a Bronze 100% append-only/auditável sem precisar
    de lógica extra de "qual child pertence a qual execução".
    """
    pendentes = buscar_produtos_pendentes(tenant_id, pipeline, limite)
    if not pendentes:
        return {"processados": 0}

    agora = datetime.now()
    ids_processados = []

    for p in pendentes:
        codigo_produto = p["codigo"]

        _upsert_produto(tenant_id, codigo_produto, p, agora)

        precos = buscar_precos_do_produto(tenant_id, codigo_produto)
        for preco in _mais_recente_por_chave(precos, "codigo_empresa").values():
            _upsert_preco(tenant_id, codigo_produto, preco, agora)

        quantidades = buscar_quantidade_do_produto(tenant_id, codigo_produto)
        for qtd in _mais_recente_por_chave(quantidades, "codigo_empresa").values():
            _upsert_empresa(tenant_id, codigo_produto, qtd, agora)

        modelos = buscar_modelos_do_produto(tenant_id, codigo_produto)
        for modelo in _mais_recente_por_chave(modelos, "codigo_modelo").values():
            _upsert_modelo(tenant_id, codigo_produto, modelo, agora)

        ids_processados.append(p["id"])

    marcar_processado("produto_sances_raw", ids_processados)

    logger.info(f"[SILVER estoque] tenant={tenant_id} | {len(ids_processados)} produtos processados.")
    return {"processados": len(ids_processados)}
