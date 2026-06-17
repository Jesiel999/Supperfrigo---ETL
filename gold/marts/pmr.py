import logging
from core.logger import get_layer_logger
from repositories.financeiro_repository import buscar_bi_para_pmr_gold, upsert_pmr_gold

logger = get_layer_logger("gold", "pmr")


def processar_pmr() -> dict:
    """
    Lê financeiro_bi (registros RECEBER)
    e grava na tabela pmr_gold.
    """
    logger.info("Iniciando processamento da camada Gold — Prazo medio recebimento")

    registros_bi = buscar_bi_para_pmr_gold()
    logger.info(f"Registros BI encontrados: {len(registros_bi)}")
    if not registros_bi:
        logger.info("Nenhum registro encontrado para prazo medio de recebimento.")
        return {"processados": 0}

    gold_registros = []

    for bi in registros_bi:
        try:
            gold = {
                "codigo_titulo":            bi.get("codigo_raw"),
                "id_empresa":               bi.get("id_empresa"),
                "id_pessoa":                bi.get("id_pessoa"),
                "numero_documento":         bi.get("numero_documento"),
                "ordem":                    bi.get("ordem"),
                "origem":                   bi.get("origem"),
                "descricao_forma_cobranca": bi.get("descricao_forma_cobranca"),
                "valor_total":              bi.get("valor_total"),
                "data_emissao":             bi.get("data_emissao"),
                "data_vencimento":          bi.get("data_vencimento"),
                "data_baixa":               bi.get("data_baixa"),
                "status_financeiro":        bi.get("status_financeiro"),
                "descricao_situacao":       bi.get("descricao_situacao"),
                "dias_recebimento":         bi.get("dias_recebimento"),
            }
            gold_registros.append(gold)
        except Exception as e:
            logger.error(f"Erro ao montar gold id_pessoa={bi.get('id_pessoa')}: {e}")

    resultado = upsert_pmr_gold(gold_registros)

    logger.info(f"Gold prazo medio recebimento: {resultado}")
    return {"processados": len(gold_registros), **resultado}
