from datetime import datetime

from core.logger import get_layer_logger
from repositories.sances.pos_venda_repository import (
    buscar_pos_venda_pendentes,
    buscar_filhos_lote,
    contar_pos_venda_pendentes,
    marcar_processado,
    upsert_pos_venda_bi_principal,
    upsert_pos_venda_bi_filhos,
)

logger = get_layer_logger("silver", "pos_venda_transform")

MAPEAMENTO_FILHOS = {
    "pos_venda_peca_raw": "pos_venda_peca_bi",
    "pos_venda_servico_raw": "pos_venda_servico_bi",
    "pos_venda_nota_raw": "nota_bi",
    "pos_venda_parcela_raw": "pos_venda_parcela_bi",
}

def _margem(lucro, bruto) -> float | None:
    if not bruto:
        return None
    try:
        return round((lucro or 0) / bruto, 4)
    except ZeroDivisionError:
        return None


def _montar_bi(raw: dict, tenant_id: int) -> dict:
    total_pecas_bruto = raw.get("total_pecas_bruto") or 0
    total_pecas_lucro = raw.get("total_pecas_lucro") or 0
    total_servicos_bruto = raw.get("total_servicos_bruto") or 0
    total_servicos_lucro = raw.get("total_servicos_lucro") or 0
    total_geral = raw.get("total_geral") or 0
    lucro_total = total_pecas_lucro + total_servicos_lucro

    data_ref = raw.get("data_insercao") or datetime.now()
    if isinstance(data_ref, datetime):
        ano, mes = data_ref.year, data_ref.month
    else:
        ano, mes = datetime.now().year, datetime.now().month

    return {
        "tenant_id": tenant_id,
        "codigo_origem": raw["codigo"],   # raw.codigo -> bi.codigo_origem
        "tipo": raw.get("tipo"),
        "descricao_tipo": raw.get("descricao_tipo"),
        "orcamento_os": raw.get("orcamento_os"),
        "numero": raw.get("numero"),
        "codigo_situacao": raw.get("codigo_situacao"),
        "situacao": raw.get("situacao"),
        "aguardando_liberacao": raw.get("aguardando_liberacao"),
        "codigo_empresa": raw.get("codigo_empresa"),
        "codigo_cliente": raw.get("codigo_cliente"),
        "codigo_tipo_preco": raw.get("codigo_tipo_preco"),
        "descricao_tipo_preco": raw.get("descricao_tipo_preco"),
        "codigo_veiculo": raw.get("codigo_veiculo"),
        "codigo_tipo_os": raw.get("codigo_tipo_os"),
        "km_entrada": raw.get("km_entrada"),
        "km_saida": raw.get("km_saida"),
        "data_entrada": raw.get("data_entrada"),
        "data_saida": raw.get("data_saida"),
        "solicitacao_cliente": raw.get("solicitacao_cliente"),
        "avaria": raw.get("avaria"),
        "defeito_averiguado": raw.get("defeito_averiguado"),
        "codigo_proprietario": raw.get("codigo_proprietario"),
        "codigo_tipo_midia": raw.get("codigo_tipo_midia"),
        "descricao_tipo_midia": raw.get("descricao_tipo_midia"),
        "codigo_modalidade_venda": raw.get("codigo_modalidade_venda"),
        "descricao_modalidade_venda": raw.get("descricao_modalidade_venda"),
        "codigo_conveniado": raw.get("codigo_conveniado"),
        "codigo_consultor": raw.get("codigo_consultor"),
        "percentual_comissao_peca": raw.get("percentual_comissao_peca"),
        "valor_comissao_peca_consultor": raw.get("valor_comissao_peca_consultor"),
        "percentual_comissao_servico": raw.get("percentual_comissao_servico"),
        "valor_comissao_servico_consultor": raw.get("valor_comissao_servico_consultor"),
        "total_comissao_consultor": raw.get("total_comissao_consultor"),
        "codigo_usuario_insercao": raw.get("codigo_usuario_insercao"),
        "data_insercao": raw.get("data_insercao"),
        "codigo_usuario_alteracao": raw.get("codigo_usuario_alteracao"),
        "data_alteracao": raw.get("data_alteracao"),
        "codigo_usuario_cancelamento": raw.get("codigo_usuario_cancelamento"),
        "data_cancelamento": raw.get("data_cancelamento"),
        "codigo_usuario_fechamento": raw.get("codigo_usuario_fechamento"),
        "data_fechamento": raw.get("data_fechamento"),
        "valor_seguro": raw.get("valor_seguro"),
        "valor_frete": raw.get("valor_frete"),
        "valor_despesas": raw.get("valor_despesas"),
        "valor_acrescimo_financeiro": raw.get("valor_acrescimo_financeiro"),
        "total_pecas_bruto": raw.get("total_pecas_bruto"),
        "total_desconto_pecas": raw.get("total_desconto_pecas"),
        "total_pecas_liquido": raw.get("total_pecas_liquido"),
        "total_pecas_custo": raw.get("total_pecas_custo"),
        "total_pecas_lucro": raw.get("total_pecas_lucro"),
        "total_servicos_bruto": raw.get("total_servicos_bruto"),
        "total_desconto_servicos": raw.get("total_desconto_servicos"),
        "total_servicos_liquido": raw.get("total_servicos_liquido"),
        "total_servicos_custo": raw.get("total_servicos_custo"),
        "total_servicos_lucro": raw.get("total_servicos_lucro"),
        "total_geral": raw.get("total_geral"),
        "codigo_condicao_pagamento": raw.get("codigo_condicao_pagamento"),
        "margem_pecas": _margem(total_pecas_lucro, total_pecas_bruto),
        "margem_servicos": _margem(total_servicos_lucro, total_servicos_bruto),
        "margem_total": _margem(lucro_total, total_geral),
        "ano": ano,
        "mes": mes,
        "mes_ano": f"{ano:04d}-{mes:02d}",
    }


def _limpar_filhos(linhas: list[dict]) -> list[dict]:
    """Remove colunas de controle do raw; mantém 'seq' (chave do upsert)."""
    limpas = []
    for linha in linhas:
        linha = dict(linha)
        linha.pop("id", None)
        linha.pop("codposv", None)
        limpas.append(linha)
    return limpas

def processar_um_pos_venda(
    tenant_id: int,
    raw: dict,
    tamanho_lote_filhos: int = 200,
) -> None:

    codigo = raw["codigo"]

    # 1. Monta e grava o principal.
    bi = _montar_bi(raw, tenant_id)

    upsert_pos_venda_bi_principal(
        tenant_id=tenant_id,
        codigo_origem=codigo,
        bi=bi,
    )

    # 2. Processa uma tabela filha por vez.
    for tabela_raw, tabela_bi in MAPEAMENTO_FILHOS.items():

        ultimo_seq = -1

        while True:

            linhas = buscar_filhos_lote(
                tenant_id=tenant_id,
                codigo=codigo,
                tabela=tabela_raw,
                limite=tamanho_lote_filhos,
                ultimo_seq=ultimo_seq,
            )

            if not linhas:
                break

            # O último seq será utilizado na próxima consulta.
            ultimo_seq = linhas[-1]["seq"]

            # Remove somente os campos de controle do raw.
            filhos = _limpar_filhos(linhas)

            # Grava imediatamente o lote no Silver.
            upsert_pos_venda_bi_filhos(
                tenant_id=tenant_id,
                codigo_origem=codigo,
                tabela=tabela_bi,
                linhas=filhos,
            )

            del filhos
            del linhas

TAMANHO_BLOCO = 20
TAMANHO_LOTE_FILHOS = 200


def processar_pos_venda_pendentes(
    tenant_id: int,
    limite: int | None = None,
) -> dict:
    """
    Processa TODOS os pendentes (limite=None) ou até `limite` registros.

    Usa cursor por id: um registro com erro é tentado uma única vez por
    execução e não bloqueia os demais. Ele permanece com processado_em NULL
    e será tentado novamente na próxima execução.
    """

    total = 0
    erros = 0
    ultimo_id = 0
    ids_com_erro: list[int] = []

    while True:

        if limite is None:
            quantidade = TAMANHO_BLOCO
        else:
            restante = limite - total - erros
            if restante <= 0:
                break
            quantidade = min(TAMANHO_BLOCO, restante)

        pendentes = buscar_pos_venda_pendentes(
            tenant_id=tenant_id,
            limite=quantidade,
            ultimo_id=ultimo_id,
        )

        if not pendentes:
            break

        # Avança o cursor ANTES de processar: falhas não são relidas.
        ultimo_id = pendentes[-1]["id"]

        for raw in pendentes:

            try:
                processar_um_pos_venda(
                    tenant_id=tenant_id,
                    raw=raw,
                    tamanho_lote_filhos=TAMANHO_LOTE_FILHOS,
                )

                marcar_processado(
                    tenant_id=tenant_id,
                    registros=[(raw["id"], raw.get("hash_registro"))],
                )

                total += 1

            except Exception:
                erros += 1
                ids_com_erro.append(raw["id"])

                logger.exception(
                    "Erro no pós-venda tenant=%s id=%s codigo=%s",
                    tenant_id,
                    raw.get("id"),
                    raw.get("codigo"),
                )

        del pendentes

    restantes = contar_pos_venda_pendentes(tenant_id)

    logger.info(
        "Silver pós-venda: tenant=%s processados=%s erros=%s restantes=%s",
        tenant_id, total, erros, restantes,
    )

    if erros:
        logger.warning(
            "Silver pós-venda: %s registro(s) com erro seguem pendentes. "
            "Exemplos de id: %s",
            erros, ids_com_erro[:10],
        )

    return {
        "processados": total,
        "erros": erros,
        "pendentes_restantes": restantes,
    }