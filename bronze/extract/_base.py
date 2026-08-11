import time
import logging
import requests

from requests.exceptions import ConnectionError, Timeout, RequestException

from repositories.offset_repository import ler_offset, salvar_offset, resetar_offset


class RateLimitAtingido(Exception):
    """Exceção utilizada para encerrar a extração quando atinge rate limit."""
    pass


def _fetch_page(url, headers, params, timeout, offset, tenant_id, origem, logger):
    response = None

    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            logger.info(f"[{origem}] GET {response.url} -> {response.status_code}")

            if response.status_code == 429:
                logger.warning(f"[{origem}] Rate limit atingido na página {offset}. Salvando offset.")
                salvar_offset(tenant_id, origem, offset)
                raise RateLimitAtingido(f"Rate limit atingido na página {offset}")

            if response.status_code == 200:
                break

            logger.error(f"[{origem}] Erro HTTP {response.status_code} na página {offset}: {response.text[:300]}")
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
        corpo = response.json()
    except Exception as e:
        logger.error(f"[{origem}] Erro ao parsear JSON da página {offset}: {e}")
        salvar_offset(tenant_id, origem, offset)
        return None

    # Alguns endpoints (Sults) devolvem uma lista pura no nível raiz.
    # Aceita os dois formatos.
    if isinstance(corpo, list):
        return corpo
    if isinstance(corpo, dict):
        return corpo.get("dados", [])

    logger.error(f"[{origem}] Formato de resposta inesperado na página {offset}: {type(corpo)}")
    salvar_offset(tenant_id, origem, offset)
    return None


def extrair_paginado(
    url: str,
    headers: dict,
    origem: str,
    tenant_id: int,
    logger: logging.Logger,
    campos_permitidos: list[str] | None = None,
    chave_obrigatoria: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
    extra_params: dict | None = None,
    timeout: int = 30,
    sleep_request: float = 1.0,
    nome_param_pagina: str = "offset",
    valor_padrao_pagina: int = 1,
    on_page=None,
) -> list[dict]:
    """
    Extrator paginado genérico
    """
    params_extra = extra_params.copy() if extra_params else {}
    offset = ler_offset(tenant_id, origem, offset_inicial, valor_padrao=valor_padrao_pagina)
    todos_registros: list[dict] = []

    while True:
        params = {"limit": limit, nome_param_pagina: offset, **params_extra}

        try:
            dados = _fetch_page(url, headers, params, timeout, offset, tenant_id, origem, logger)
        except RateLimitAtingido:
            logger.warning(
                f"[{origem}] Extração interrompida por rate limit. "
                f"Retornando {len(todos_registros)} registros já coletados."
            )
            break

        if dados is None:
            logger.warning(f"[{origem}] Extração encerrada com falha. Offset salvo para retomada.")
            break

        # Lista vazia = fim dos dados.
        if not dados:
            logger.info(f"[{origem}] Página {offset} vazia — fim dos registros. Total: {len(todos_registros)}")
            resetar_offset(tenant_id, origem, valor_padrao=valor_padrao_pagina)
            break

        logger.info(f"[{origem}] Página {offset}: {len(dados)} registros recebidos.")

        for item in dados:
            filtrado = {campo: item.get(campo) for campo in campos_permitidos}
            if filtrado.get(chave_obrigatoria):
                todos_registros.append(filtrado)

        # Salva progresso e avança — se o processo morrer no meio, não perde a página atual.
        salvar_offset(tenant_id, origem, offset)
        time.sleep(sleep_request)
        offset += 1

    logger.info(f"[{origem}] Extração finalizada | tenant={tenant_id} | registros={len(todos_registros)}")
    return todos_registros

def extrair_paginado_estoque(
    url: str,
    headers: dict,
    origem: str,
    tenant_id: int,
    on_page,  
    logger: logging.Logger,
    limit: int = 100,
    offset_inicial: int | None = None,
    extra_params: dict | None = None,
    timeout: int = 30,
    sleep_request: float = 1.0,
    nome_param_pagina: str = "offset",
    valor_padrao_pagina: int = 1,
) -> dict:
    params_extra = extra_params.copy() if extra_params else {}
    offset = ler_offset(tenant_id, origem, offset_inicial, valor_padrao=valor_padrao_pagina)
    paginas = 0
    total_registros = 0

    while True:
        params = {"limit": limit, nome_param_pagina: offset, **params_extra}

        try:
            dados = _fetch_page(url, headers, params, timeout, offset, tenant_id, origem, logger)
        except RateLimitAtingido:
            logger.warning(f"[{origem}] Extração interrompida por rate limit na página {offset}.")
            return {"paginas": paginas, "registros": total_registros, "status": "RATE_LIMIT"}

        if dados is None:
            logger.warning(f"[{origem}] Extração encerrada com falha na página {offset}. Offset NÃO avançado.")
            return {"paginas": paginas, "registros": total_registros, "status": "ERRO"}

        qtd = len(dados)

        # Fim da paginação: página sem registros.
        if qtd == 0:
            logger.info(f"[{origem}] Página {offset} vazia — fim dos registros. Total: {total_registros}")
            resetar_offset(tenant_id, origem, valor_padrao=valor_padrao_pagina)
            return {"paginas": paginas, "registros": total_registros, "status": "CONCLUIDO"}

        # Persiste a página ANTES de avançar o offset — se isso falhar, o
        # offset fica exatamente onde estava, e a próxima execução reprocessa
        # esta mesma página (não perde nem duplica).
        try:
            on_page(dados, offset, limit)
        except Exception as e:
            logger.error(f"[{origem}] Falha ao persistir página {offset} na Bronze: {e}. Offset NÃO avançado.")
            return {"paginas": paginas, "registros": total_registros, "status": "ERRO"}

        logger.info(f"[{origem}] Página {offset}: {qtd} registros persistidos na Bronze.")
        paginas += 1
        total_registros += qtd

        salvar_offset(tenant_id, origem, offset)
        time.sleep(sleep_request)
        offset += 1


def _fetch_um(url, headers, timeout, codigo, tenant_id, origem, logger):
    """Busca um único registro por código. Retorna o dict de "dados", ou None se não existir/falhar."""
    response = None

    while True:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            logger.info(f"[{origem}] GET {response.url} -> {response.status_code}")

            if response.status_code == 429:
                logger.warning(f"[{origem}] Rate limit atingido no código {codigo}. Salvando offset.")
                salvar_offset(tenant_id, origem, codigo)
                raise RateLimitAtingido(f"Rate limit atingido no código {codigo}")

            if response.status_code == 404:
                # Código não existe (cliente nunca cadastrado, ou cancelado/removido) — não é erro, só não há dados.
                return None

            if response.status_code == 200:
                break

            logger.error(f"[{origem}] Erro HTTP {response.status_code} no código {codigo}: {response.text[:300]}")
            return None

        except Timeout:
            logger.warning(f"[{origem}] Timeout no código {codigo}. Aguardando 5s e tentando de novo...")
            time.sleep(5)

        except ConnectionError:
            logger.warning(f"[{origem}] Erro de conexão no código {codigo}. Aguardando 5s...")
            time.sleep(5)

        except RequestException as e:
            logger.error(f"[{origem}] Erro de request inesperado no código {codigo}: {e}")
            time.sleep(5)

    try:
        corpo = response.json()
    except Exception as e:
        logger.error(f"[{origem}] Erro ao parsear JSON do código {codigo}: {e}")
        return None

    if not corpo.get("sucesso", True):
        logger.info(f"[{origem}] Código {codigo}: sucesso=false ({corpo.get('mensagemUsuarioFinal')}).")
        return None

    return corpo.get("dados")


def extrair_por_codigo(
    url_base: str,
    headers: dict,
    origem: str,
    tenant_id: int,
    campos_permitidos: list[str],
    logger: logging.Logger,
    offset_inicial: int | None = None,
    quantidade_por_execucao: int = 5000,
    timeout: int = 30,
    sleep_request: float = 1.0,
    max_nao_encontrados_seguidos: int = 5000,
) -> list[dict]:
    codigo = ler_offset(tenant_id, origem, offset_inicial)
    todos_registros: list[dict] = []
    nao_encontrados_seguidos = 0

    for _ in range(quantidade_por_execucao):
        url = f"{url_base}?codigo_cliente={codigo}"

        try:
            item = _fetch_um(url, headers, timeout, codigo, tenant_id, origem, logger)
        except RateLimitAtingido:
            logger.warning(
                f"[{origem}] Extração interrompida por rate limit no código {codigo}. "
                f"{len(todos_registros)} registros coletados nesta execução."
            )
            break

        if item is None:
            nao_encontrados_seguidos += 1
            if nao_encontrados_seguidos >= max_nao_encontrados_seguidos:
                logger.info(
                    f"[{origem}] {max_nao_encontrados_seguidos} códigos seguidos sem retorno "
                    f"(parou em {codigo}) — encerrando varredura desta execução."
                )
                codigo += 1
                salvar_offset(tenant_id, origem, codigo)
                break
        else:
            nao_encontrados_seguidos = 0
            filtrado = {campo: item.get(campo) for campo in campos_permitidos}
            todos_registros.append(filtrado)

        codigo += 1
        salvar_offset(tenant_id, origem, codigo)
        time.sleep(sleep_request)

    logger.info(
        f"[{origem}] Extração finalizada | tenant={tenant_id} | "
        f"registros={len(todos_registros)} | próximo código={codigo}"
    )
    return todos_registros