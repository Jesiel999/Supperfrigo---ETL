from datetime import datetime
from core.logger import get_layer_logger

logger = get_layer_logger("silver", "chamados")


def _to_datetime(valor):
    """
    Converte strings ISO 8601 para datetime.
    Formatos suportados:
    - 2022-06-27T13:15:26Z
    - 2022-06-27T13:15:26.000Z
    - 2022-06-27 13:15:26
    """
    
    if not valor:
        return None
    
    if isinstance(valor, datetime):
        return valor
    
    try:
        valor = (
            str(valor)
            .replace("T", " ")
            .replace("Z", "")
            .split(".")[0]
        )
        
        return datetime.strptime(
            valor,
            "%Y-%m-%d %H:%M:%S"
        )
    
    except Exception:
        return None


def transformar_chamados(
    chamados_raw: list,
    apoios_raw: list,
    etiquetas_raw: list,
    tenant_id: int
) -> dict:
    """
    Transforma registros da Bronze (Raw) para Silver (BI).
    
    Args:
        chamados_raw: Lista de dicts com dados do chamados_raw
        apoios_raw: Lista de dicts com dados do chamados_apoio_raw
        etiquetas_raw: Lista de dicts com dados do chamados_etiqueta_raw
        tenant_id: ID do tenant para filtragem
    
    Returns:
        Dict com três listas: chamados_bi, apoios_bi, etiquetas_bi
    """
    
    chamados_bi = []
    apoios_bi = []
    etiquetas_bi = []
    
    # ========================
    # TRANSFORM: chamados_raw -> chamados_bi
    # ========================
    
    for raw in chamados_raw:
        
        try:
            if raw.get("tenant_id") != tenant_id:
                continue
            
            codigo = raw.get("codigo")
            
            if not codigo:
                logger.warning(f"Registro raw sem código — ignorado")
                continue
            
            # Converte datas
            aberto = _to_datetime(raw.get("data_aberto"))
            resolvido = _to_datetime(raw.get("data_resolvido"))
            concluido = _to_datetime(raw.get("data_concluido"))
            resolver_planejado = _to_datetime(raw.get("data_resolver_planejado"))
            resolver_estipulado = _to_datetime(raw.get("data_resolver_estipulado"))
            primeira_interacao = _to_datetime(raw.get("data_primeira_interacao"))
            ultima_alteracao = _to_datetime(raw.get("data_ultima_alteracao"))
            
            # Calcula tempos (em horas)
            tempo_primeira_resposta = None
            tempo_resolucao = None
            
            if aberto and primeira_interacao:
                delta = primeira_interacao - aberto
                tempo_primeira_resposta = int(delta.total_seconds() / 3600)
            
            if aberto and resolvido:
                delta = resolvido - aberto
                tempo_resolucao = int(delta.total_seconds() / 3600)
            
            # Calcula SLA (assumindo 24h padrão)
            sla_horas = 24
            sla_cumprido = False
            horas_atrasado = None
            horas_resolver = None
            
            if resolver_estipulado and ultima_alteracao:
                delta = ultima_alteracao - resolver_estipulado
                horas_resolver = delta.total_seconds() / 3600
                sla_cumprido = horas_resolver <= 0
                if horas_resolver > 0:
                    horas_atrasado = horas_resolver
            
            chamado_bi = {
                "codigo_raw": codigo,
                "titulo": raw.get("titulo"),
                
                # Relacionamentos
                "solicitante_id": raw.get("solicitante_id"),
                "responsavel_id": raw.get("responsavel_id"),
                "unidade_id": raw.get("unidade_id"),
                "departamento_id": raw.get("departamento_id"),
                "departamento_envio_id": raw.get("departamento_envio_id"),
                "assunto_id": raw.get("assunto_id"),
                
                # Tipo e Situação
                "tipo": raw.get("tipo"),
                "situacao": raw.get("situacao"),
                
                # Datas
                "data_aberto": aberto,
                "data_resolvido": resolvido,
                "data_concluido": concluido,
                "data_resolver_planejado": resolver_planejado,
                "data_resolver_estipulado": resolver_estipulado,
                "data_primeira_interacao": primeira_interacao,
                "data_ultima_alteracao": ultima_alteracao,
                
                # Avaliação
                "avaliacao_nota": raw.get("avaliacao_nota"),
                "avaliacao_observacao": raw.get("avaliacao_observacao"),
                
                # Contadores de interação
                "quantidade_interacao_publico": raw.get("quantidade_interacao_publico", 0),
                "quantidade_interacao_interno": raw.get("quantidade_interacao_interno", 0),
                
                # Campos calculados
                "tempo_primeira_resposta": tempo_primeira_resposta,
                "tempo_resolucao": tempo_resolucao,
                "sla_horas": sla_horas,
                "sla_cumprido": sla_cumprido,
                "horas_atrasado": horas_atrasado,
                "horas_resolver": horas_resolver,
                "tipo_solicitacao": _mapear_tipo_solicitacao(raw.get("tipo")),
            }
            
            chamados_bi.append(chamado_bi)
        
        except Exception as e:
            logger.error(
                f"Erro ao transformar chamado {raw.get('codigo')}: {e}",
                exc_info=True
            )
    
    # ========================
    # TRANSFORM: chamados_apoio_raw -> chamados_apoio_bi
    # ========================
    
    apoios_unicos = set()

    for raw in apoios_raw:
        try:
            if raw.get("tenant_id") != tenant_id:
                continue

            chamado_codigo = raw.get("chamado_codigo")
            pessoa_id = raw.get("pessoa_id")
            departamento_id = raw.get("departamento_id")

            if not chamado_codigo or not pessoa_id:
                logger.warning("Apoio raw sem chave mínima — ignorado")
                continue

            chave = (chamado_codigo, pessoa_id, departamento_id)

            if chave in apoios_unicos:
                continue

            apoios_unicos.add(chave)

            apoio_bi = {
                "chamado_codigo": chamado_codigo,
                "pessoa_id": pessoa_id,
                "departamento_id": departamento_id,
            }

            apoios_bi.append(apoio_bi)

        except Exception as e:
            logger.error(
                f"Erro ao transformar apoio {raw.get('chamado_codigo')}: {e}",
                exc_info=True
            )
    
    # ========================
    # TRANSFORM: chamados_etiqueta_raw -> chamados_etiqueta_bi
    # ========================
    
    for raw in etiquetas_raw:
        
        try:
            if raw.get("tenant_id") != tenant_id:
                continue
            
            codigo = raw.get("chamado_codigo")
            etiqueta_id = raw.get("etiqueta_id")
            
            if not codigo or not etiqueta_id:
                logger.warning(f"Etiqueta raw inválida — ignorada")
                continue
            
            etiqueta_bi = {
                "chamado_codigo": codigo,
                "etiqueta_id": etiqueta_id,
            }
            
            etiquetas_bi.append(etiqueta_bi)
        
        except Exception as e:
            logger.error(
                f"Erro ao transformar etiqueta {raw.get('chamado_codigo')}: {e}",
                exc_info=True
            )
    
    logger.info(
        f"Silver Transform concluído: "
        f"{len(chamados_bi)} chamados | "
        f"{len(apoios_bi)} apoios | "
        f"{len(etiquetas_bi)} etiquetas"
    )
    
    return {
        "chamados": chamados_bi,
        "apoios": apoios_bi,
        "etiquetas": etiquetas_bi,
    }


def _mapear_tipo_solicitacao(tipo_id: int) -> str:
    """
    Mapeia tipo ID para descrição textual.
    Customize conforme sua negócio.
    """
    
    tipo_map = {
        1: "Dúvida",
        2: "Problema",
        3: "Sugestão",
        4: "Reclamação",
        5: "Elogio",
    }
    
    return tipo_map.get(tipo_id, "Outro")