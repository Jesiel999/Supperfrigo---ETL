from datetime import date, datetime
from core.logger import get_layer_logger
from repositories.sances.pos_venda_repository import buscar_pos_venda_pendentes, buscar_filhos, marcar_processado, upsert_pos_venda_bi

logger = get_layer_logger("silver", "pos_venda_transform")


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
        "codigo_origem": raw["codigo_origem"],
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
        "descricao_tipo_os": raw.get("descricao_tipo_os"),
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
        "descricao_condicao_pagamento": raw.get("descricao_condicao_pagamento"),
        "margem_pecas": _margem(total_pecas_lucro, total_pecas_bruto),
        "margem_servicos": _margem(total_servicos_lucro, total_servicos_bruto),
        "margem_total": _margem(lucro_total, total_geral),
        "ano": ano,
        "mes": mes,
        "mes_ano": f"{ano:04d}-{mes:02d}",
        "data_carga": datetime.now(),
    }


def processar_pos_venda_pendentes(tenant_id: int, limite: int = 500) -> dict:
    pendentes = buscar_pos_venda_pendentes(tenant_id, limite)
    if not pendentes:
        return {"processados": 0}

    ids_processados = []

    for raw in pendentes:
        codigo_origem = raw["codigo_origem"]
        bi = _montar_bi(raw, tenant_id)

        pecas = buscar_filhos("pos_venda_peca_raw", tenant_id, codigo_origem)
        servicos = buscar_filhos("pos_venda_servico_raw", tenant_id, codigo_origem)
        notas = buscar_filhos("pos_venda_nota_raw", tenant_id, codigo_origem)
        parcelas = buscar_filhos("pos_venda_parcela_raw", tenant_id, codigo_origem)

        for lista in (pecas, servicos, notas, parcelas):
            for linha in lista:
                linha.pop("id", None)
                linha.pop("codposv", None)

        upsert_pos_venda_bi(
            tenant_id=tenant_id,
            codigo_origem=codigo_origem,
            bi=bi,
            filhos={"pecas": pecas, "servicos": servicos, "notas": notas, "parcelas": parcelas},
        )
        ids_processados.append(raw["id"])

    marcar_processado(ids_processados)
    # logger.info(f"[SILVER pos_venda] tenant={tenant_id} | {len(ids_processados)} pós-vendas processados.")
    return {"processados": len(ids_processados)}