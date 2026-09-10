import requests
import time
import logging

from requests.exceptions import ConnectionError, Timeout, RequestException
from datetime import datetime
from repositories.sances.financeiro_repository import salvar_pagina_raw
from bronze.extract._base import extrair_paginado_sem_filtro
from config.settings import SANCES_TOKEN, URL_SANCES_FINANCEIRO, REQUEST_TIMEOUT, RATE_LIMIT_SLEEP, SLEEP_REQUEST
from core.logger import get_layer_logger
from repositories.offset_repository import ler_offset, salvar_offset, resetar_offset

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

def _normalizar(valor) -> str:
    if valor is None:
        return ""
    valor = str(valor).strip().replace("T", " ")
    if "+" in valor:
        valor = valor.split("+")[0]
    if "Z" in valor:
        valor = valor.replace("Z", "")
    if "." in valor:
        valor = valor.split(".")[0]
    return valor.strip()

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

def _fetch_page(
    limit: int,
    offset: int,
    tenant_id: int,
    origem: str,
    extra_params: dict | None = None,
    offset_file: str | None = None,
) -> list[dict] | None:
    params = {"limit": limit, "offset": offset}
    if extra_params:
        params.update(extra_params)

    response = None

    while True:
        try:
            response = requests.get(
                URL_SANCES_FINANCEIRO,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            logger.info(f"[{origem}] GET {response.url} -> {response.status_code}")

            # ==========================================
            # RATE LIMIT — aguarda e tenta de novo
            # ==========================================
            if response.status_code == 429:
                logger.warning(
                    f"[{origem}] Rate limit atingido na página {offset}. "
                    f"Encerrando Bronze e salvando offset para continuação futura."
                )
                salvar_offset(tenant_id, origem, offset)
                raise RateLimitAtingido(
                    f"Rate limit atingido na página {offset}"
                )

            if response.status_code == 200:
                break

            # ==========================================
            # ERRO HTTP DEFINITIVO
            # ==========================================
            logger.error(
                f"[{origem}] Erro HTTP {response.status_code} na página {offset}: "
                f"{response.text[:300]}"
            )
            salvar_offset(tenant_id, origem, offset)
            return None

        except Timeout:
            logger.warning(f"[{origem}] Timeout na página {offset}. Aguardando 5s e tentando de novo...")
            time.sleep(5)

        except ConnectionError:
            logger.warning(f"[{origem}] Erro de conexão na página {offset}. Aguardando 5s...")
            time.sleep(5)

        except RequestException as e:
            logger.error(f"[{origem}] Erro de request inesperado na página {offset}: {e}")
            time.sleep(5)

    try:
        dados = response.json().get("dados", [])
        return dados
    except Exception as e:
        logger.error(f"[{origem}] Erro ao parsear JSON da página {offset}: {e}")
        salvar_offset(tenant_id, origem, offset)
        return None

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

def extrair_financeiro(
    tenant_id: int,
    origem: str,
    limit: int = 100,
    offset_inicial: int | None = None,
    extra_params: dict | None = None,
    data_vencimento_inicial: str | None = None,
    data_vencimento_final: str | None = None,
    data_insercao_inicial: str | None = None,
    data_insercao_final: str | None = None,
    codigo_situacao: str | None = None,
) -> dict:
    params_extra: dict = extra_params.copy() if extra_params else {}

    if data_vencimento_inicial:
        params_extra["data_vencimento_inicial"] = data_vencimento_inicial
        logger.info(f"[{origem}] Filtro data_vencimento_inicial: {data_vencimento_inicial}")

    if data_vencimento_final:
        params_extra["data_vencimento_final"] = data_vencimento_final
        logger.info(f"[{origem}] Filtro data_vencimento_final: {data_vencimento_final}")

    if data_insercao_inicial:
        params_extra["data_insercao_inicial"] = data_insercao_inicial
        logger.info(f"[{origem}] Filtro data_insercao_inicial: {data_insercao_inicial}")

    if data_insercao_final:
        params_extra["data_insercao_final"] = data_insercao_final
        logger.info(f"[{origem}] Filtro data_insercao_final: {data_insercao_final}")

    if codigo_situacao:
        params_extra["codigo_situacao"] = codigo_situacao
        logger.info(f"[{origem}] Filtro de situacao: {codigo_situacao}")

    offset = ler_offset(tenant_id, origem, offset_inicial, valor_padrao=1)

    todos_registros: list[dict] = []
    status = "ERRO"  # assume erro até provar o contrário

    while True:
        try:
            dados = _fetch_page(
                limit=limit,
                offset=offset,
                tenant_id=tenant_id,
                origem=origem,
                extra_params=params_extra if params_extra else None,
            )
        except RateLimitAtingido:
            logger.warning(
                f"[{origem}] Extração interrompida por rate limit. "
                f"Retornando {len(todos_registros)} registros já coletados."
            )
            status = "RATE_LIMIT"
            break

        # FALHA DEFINITIVA NA API
        if dados is None:
            logger.warning(
                f"[{origem}] Extração encerrada com falha. "
                "Execute novamente para retomar do ponto de parada."
            )
            status = "ERRO"
            break

        # FIM DOS DADOS
        if not dados:
            logger.info(
                f"[{origem}] Página {offset} veio vazia (situacao={codigo_situacao}) — fim dos registros. "
                f"Total extraído: {len(todos_registros)} registros."
            )
            status = "CONCLUIDO"
            resetar_offset(tenant_id, origem, valor_padrao=1)
            break

        logger.info(f"[{origem}] Página {offset} (situacao={codigo_situacao}): {len(dados)} registros recebidos.")

        for item in dados:
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

        salvar_offset(tenant_id, origem, offset)
        time.sleep(SLEEP_REQUEST)
        offset += 1

    logger.info(
        f"[{origem}] Extração finalizada | situacao={codigo_situacao} | "
        f"registros={len(todos_registros)} | status={status}"
    )
    return {"registros": todos_registros, "status": status}
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
