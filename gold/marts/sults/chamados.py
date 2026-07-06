import logging
from core.logger import get_layer_logger
from repositories.sults.chamados_repository import (
    buscar_bi_para_chamados_geral_gold,
    upsert_chamados_geral_gold
)

logger = get_layer_logger("gold", "chamados")


def processar_chamados_geral_gold() -> dict:
    """
    Lê dados da camada Silver (chamados_bi) e carrega na camada Gold (chamados_geral_gold).
    
    A tabela Gold é truncada antes de cada carga para garantir que sempre
    reflete o estado atual dos dados.
    
    Returns:
        Dict com resumo do processamento
    """
    
    logger.info("Iniciando processamento da camada Gold — Chamados Geral")
    
    # Busca todos os registros da camada BI (Silver)
    registros_bi = buscar_bi_para_chamados_geral_gold()
    
    if not registros_bi:
        logger.info("Nenhum registro encontrado para chamados geral.")
        return {
            "processados": 0,
            "inseridos": 0,
            "erros": 0,
        }
    
    gold_registros = []
    
    for bi in registros_bi:
        
        try:
            
            # Monta registro Gold com todos os campos da Silver
            # (enriquecimento pode ser adicionado aqui conforme necessário)
            gold = {
                "codigo": bi.get("codigo_raw"),
                "titulo": bi.get("titulo"),
                
                # IDs de relacionamento
                "solicitante_id": bi.get("solicitante_id"),
                "responsavel_id": bi.get("responsavel_id"),
                "departamento_id": bi.get("departamento_id"),
                "departamento_envio_id": bi.get("departamento_envio_id"),
                "assunto_id": bi.get("assunto_id"),
                
                # Tipo e Situação
                "tipo": bi.get("tipo"),
                "situacao": bi.get("situacao"),
                
                # Datas
                "data_aberto": bi.get("data_aberto"),
                "data_resolvido": bi.get("data_resolvido"),
                "data_concluido": bi.get("data_concluido"),
                "data_resolver_planejado": bi.get("data_resolver_planejado"),
                "data_resolver_estipulado": bi.get("data_resolver_estipulado"),
                "data_primeira_interacao": bi.get("data_primeira_interacao"),
                "data_ultima_alteracao": bi.get("data_ultima_alteracao"),
                
                # Avaliação
                "avaliacao_nota": bi.get("avaliacao_nota"),
                "avaliacao_observacao": bi.get("avaliacao_observacao"),
                
                # Contadores
                "quantidade_interacao_publico": bi.get("quantidade_interacao_publico"),
                "quantidade_interacao_interno": bi.get("quantidade_interacao_interno"),
                
                # Campos calculados (já vêm da Silver)
                "tempo_primeira_resposta": bi.get("tempo_primeira_resposta"),
                "tempo_resolucao": bi.get("tempo_resolucao"),
                "sla_horas": bi.get("sla_horas"),
                "sla_cumprido": bi.get("sla_cumprido"),
                "horas_atrasado": bi.get("horas_atrasado"),
                "horas_resolver": bi.get("horas_resolver"),
                "tipo_solicitacao": bi.get("tipo_solicitacao"),
            }
            
            gold_registros.append(gold)
        
        except Exception as e:
            logger.error(f"Erro ao montar gold codigo={bi.get('codigo')}: {e}")
    
    # Carrega na tabela Gold
    resultado = upsert_chamados_geral_gold(gold_registros)
    
    logger.info(
        f"Gold chamados_geral concluído: "
        f"INSERT={resultado.get('inseridos')} "
        f"ERRO={resultado.get('erros')}"
    )
    
    return {
        "processados": len(gold_registros),
        **resultado
    }