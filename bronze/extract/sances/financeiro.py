import requests
import time
import os
import logging

from requests.exceptions import ConnectionError, Timeout, RequestException
from datetime import datetime
from repositories.sances.financeiro_repository import salvar_pagina_raw
from bronze.extract._base import extrair_paginado_sem_filtro
from config.settings import SANCES_TOKEN, URL_SANCES_FINANCEIRO, REQUEST_TIMEOUT, RATE_LIMIT_SLEEP, SLEEP_REQUEST
from core.logger import get_layer_logger

class RateLimitAtingido(Exception):
    """Exceção utilizada para encerrar a extração quando atingir rate limit."""
    pass

logger = get_layer_logger("bronze", "financeiro")

# ==========================================
# CAMPOS PERMITIDOS (título)
# ==========================================
CAMPOS_PERMITIDOS = [
    "codigo", "tipo_titulo",
    "codigo_empresa", "nome_empresa",
    "codigo_situacao", "descricao_situacao",
    "codigo_pessoa", "nome_pessoa",
    "codigo_cliente_fornecedor", "nome_cliente_fornecedor",
    "titulo_previsao", "criado_manualmente",
    "origem", "codigo_origem",
    "numero_documento", "ordem",
    "codigo_forma_cobranca", "descricao_forma_cobranca",
    "codigo_vendedor", "descricao_vendedor",
    "historico",
    "codigo_grupo", "descricao_grupo",
    "codigo_departamento", "descricao_departamento",
    "observacao", "observacoes_boleto",
    "codigo_barras",
    "codigo_forma_pagamento", "descricao_forma_pagamento",
    "codigo_categoria_financeira", "descricao_categoria_financeira",
    "codigo_convenio", "descricao_convenio",
    "codigo_conveniado", "descricao_conveniado",
    "codigo_aprovador", "nome_aprovador",
    "nosso_numero", "numero_remessa",
    "titulo_origem", "titulo_gerado",
    "codigo_conta_patrimonial", "numero_conta_patrimonial", "descricao_conta_patrimonial",
    "codigo_conta_resultado", "numero_conta_resultado", "descricao_conta_resultado",
    "codigo_centro_custo", "descricao_centro_custo",
    "data_emissao", "data_competencia", "data_vencimento",
    "codigo_usuario_insercao", "nome_usuario_insercao", "data_insercao",
    "codigo_usuario_alteracao", "nome_usuario_alteracao", "data_alteracao",
    "codigo_usuario_cancelamento", "nome_usuario_cancelamento", "data_cancelamento",
    "motivo_cancelamento",
    "codigo_usuario_baixa", "nome_usuario_baixa", "data_baixa",
    "codigo_usuario_aprovacao", "nome_usuario_aprovacao", "data_aprovacao",
    "valor_nominal", "valor_multa",
    "percentual_multa", "percentual_juros",
    "taxa_boleto", "juros_crediario_proprio",
    "acrescimo", "valor_total",
]

CAMPOS_DATA = [
    "data_emissao", "data_competencia", "data_vencimento",
    "data_insercao", "data_alteracao",
    "data_cancelamento", "data_baixa", "data_aprovacao",
    "data_pagamento",
]

# ==========================================
# HELPERS
# ==========================================

def _converter_data(data_str) -> str | None:
    if not data_str:
        return None
    try:
        data_str = (
            str(data_str).strip()
            .replace("Z", "")
            .replace("T", " ")
        )
        if "+" in data_str:
            data_str = data_str.split("+")[0]
        if "." in data_str:
            data_str = data_str.split(".")[0]
        data_str = data_str.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(data_str, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return None
    except Exception as e:
        logger.error(f"Erro converter_data | valor={data_str} | {e}")
        return None


def _filtrar_item(item: dict) -> dict:
    """Converte datas e filtra apenas campos permitidos do TÍTULO (não inclui recebimentos)."""
    for campo in CAMPOS_DATA:
        if campo in item and item[campo]:
            item[campo] = _converter_data(item[campo])

    return {k: v for k, v in item.items() if k in CAMPOS_PERMITIDOS}


def _extrair_recebimentos(item: dict, codigo_titulo, tenant_id: int) -> list[dict]:
    """
    Extrai o array 'recebimentos' do título antes da filtragem principal
    (senão seria descartado, já que não está em CAMPOS_PERMITIDOS).

    Diferente de arrays aninhados de outras pipelines (pós-venda), aqui
    cada recebimento já vem com 'codigo' próprio e estável — dá pra fazer
    upsert direto por essa chave, sem precisar de delete+insert.
    """
    recebimentos = item.get("recebimentos") or []
    
    linhas = []

    data_alteracao_titulo = _converter_data(
        item.get("data_alteracao")
    )

    for r in recebimentos:
        codigo = r.get("codigo")
        if not codigo:
            continue
        linhas.append({
            "tenant_id": tenant_id,
            "id": codigo,
            "codigo_titulo": codigo_titulo,
            "codigo_tipo_movimentacao": r.get("codigo_tipo_movimentacao"),
            "descricao_tipo_movimentacao": r.get("descricao_tipo_movimentacao"),
            "valor_pago": r.get("valor_pago"),
            "valor_nominal": r.get("valor_nominal"),
            "data_movimentacao": _converter_data(r.get("data_movimentacao")),
            "data_alteracao": data_alteracao_titulo,
            "codigo_conta": r.get("codigo_conta"),
            "descricao_conta": r.get("descricao_conta"),
            "historico": r.get("historico"),
            "data_conciliacao": _converter_data(r.get("data_conciliacao")),
            "codigo_caixa": r.get("codigo_caixa"),
            "codigo_cheque_terceiro": r.get("codigo_cheque_terceiro"),
            "codigo_pagamento_cartao": r.get("codigo_pagamento_cartao"),
            "desconto": r.get("desconto"),
            "acrescimo": r.get("acrescimo"),
            "juros": r.get("juros"),
            "multa": r.get("multa"),
        })
    return linhas


# ==========================================
# INTERFACE PÚBLICA
# ==========================================

def extrair_financeiro_sances(
    tenant_id: int,
    origem: str,
    token: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {token or SANCES_TOKEN}"}
    extra_params = filtros or {}

    def _persistir_pagina(itens: list[dict], offset: int, limit_usado: int) -> None:
        titulos_filtrados = []
        recebimentos_para_salvar = []

        for item in itens:
            codigo_titulo = item.get("codigo")
            if not codigo_titulo:
                continue

            # extrai recebimentos ANTES da filtragem (senão _filtrar_item descarta)
            recebimentos_para_salvar.extend(
                _extrair_recebimentos(item, codigo_titulo, tenant_id)
            )

            filtrado = _filtrar_item(item)
            filtrado["tenant_id"] = tenant_id
            titulos_filtrados.append(filtrado)

        salvar_pagina_raw(
            tenant_id=tenant_id,
            itens=titulos_filtrados,
            recebimentos=recebimentos_para_salvar,
        )

    return extrair_paginado_sem_filtro(
        url=URL_SANCES_FINANCEIRO,
        headers=headers,
        origem=origem,
        tenant_id=tenant_id,
        on_page=_persistir_pagina,
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        extra_params=extra_params,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
    )