import logging
from core.logger import get_layer_logger
from repositories.financeiro_repository import buscar_bi_para_inadimplencia_gold, upsert_inadimplencia_gold

logger = get_layer_logger("gold", "inadimplencia")


def processar_inadimplencia() -> dict:
    """
    Lê financeiro_bi (registros RECEBER vencidos/em aberto)
    e grava na tabela inadimplencia_gold.
    """
    logger.info("Iniciando processamento da camada Gold — Inadimplência")

    registros_bi = buscar_bi_para_inadimplencia_gold()

    if not registros_bi:
        logger.info("Nenhum registro encontrado para inadimplência.")
        return {"processados": 0}

    gold_registros = []

    for bi in registros_bi:
        try:
            gold = {
                "id_empresa":               bi.get("id_empresa"),
                "nome_empresa":             bi.get("nome_empresa"),
                "id_pessoa":                bi.get("id_pessoa"),
                "nome_pessoa":              bi.get("nome_pessoa"),
                "numero_documento":         bi.get("numero_documento"),
                "ordem":                    bi.get("ordem"),
                "origem":                   bi.get("origem"),
                "descricao_forma_cobranca": bi.get("descricao_forma_cobranca"),
                "valor_total":              bi.get("valor_total"),
                "data_vencimento":          bi.get("data_vencimento"),
                "data_baixa":               bi.get("data_baixa"),
                "dias_atraso":              bi.get("dias_atraso"),
                "status_financeiro":        bi.get("status_financeiro"),
                "descricao_situacao":       bi.get("descricao_situacao"),
            }
            gold_registros.append(gold)
        except Exception as e:
            logger.error(f"Erro ao montar gold id_pessoa={bi.get('id_pessoa')}: {e}")

    resultado = upsert_inadimplencia_gold(gold_registros)

    logger.info(f"Gold inadimplencia: {resultado}")
    return {"processados": len(gold_registros), **resultado}
