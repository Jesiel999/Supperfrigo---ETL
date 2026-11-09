import time
import gc
import logging
import requests

from requests.exceptions import ConnectionError, Timeout, RequestException

from repositories.offset_repository import ler_offset, salvar_offset, resetar_offset


class RateLimitAtingido(Exception):
    """Exceção utilizada para encerrar a extração quando atinge rate limit."""
    pass


def _fetch_page(url, headers, params, timeout, offset, tenant_id, origem, logger, max_tentativas=5):
    response = None
    tentativa = 0

    while True:
        tentativa += 1
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            # logger.info(f"[{origem}] GET {response.url} -> {response.status_code}")

            if response.status_code == 429:
                logger.warning(f"[{origem}] Rate limit atingido na página {offset}. Salvando offset.")
                salvar_offset(tenant_id, origem, offset)
                raise RateLimitAtingido(f"Rate limit atingido na página {offset}")

            if response.status_code == 200:
                break

            logger.error(f"[{origem}] Erro HTTP {response.status_code} na página {offset}: {response.text[:300]}")
            salvar_offset(tenant_id, origem, offset)
            return None

        except RequestException as e:      # inclui Timeout e ConnectionError
            if tentativa >= max_tentativas:
                logger.error(
                    f"[{origem}] Página {offset}: {type(e).__name__} após {tentativa} tentativas. "
                    f"Desistindo; offset salvo para retomada."
                )
                salvar_offset(tenant_id, origem, offset)
                return None

            espera = min(5 * 2 ** (tentativa - 1), 60)
            logger.warning(
                f"[{origem}] {type(e).__name__} na página {offset} "
                f"(tentativa {tentativa}/{max_tentativas}). Aguardando {espera}s..."
            )
            time.sleep(espera)

    # ── daqui para baixo: fora do loop, só depois do 200 ──────────────
    try:
        corpo = response.json()
    except Exception as e:
        logger.error(f"[{origem}] Erro ao parsear JSON da página {offset}: {e}")
        salvar_offset(tenant_id, origem, offset)
        return None

    if isinstance(corpo, list):
        return corpo

    if isinstance(corpo, dict):
        if corpo.get("sucesso") is False:
            logger.error(
                f"[{origem}] API sucesso=false na página {offset}: "
                f"{corpo.get('mensagemUsuarioFinal')}"
            )
            salvar_offset(tenant_id, origem, offset)
            return None

        dados = corpo.get("dados", [])
        if isinstance(dados, dict):          # formato antigo: dados dentro de dados
            dados = dados.get("dados", [])
        return dados

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
    timeout=(10, 120),
    sleep_request: float = 1.0,
    nome_param_pagina: str = "offset",
    valor_padrao_pagina: int = 1,
    max_tentativas: int = 5,
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
            #logger.warning(
            #    f"[{origem}] Extração interrompida por rate limit. "
            #    f"Retornando {len(todos_registros)} registros já coletados."
            #)
            break

        if dados is None:
            # logger.warning(f"[{origem}] Extração encerrada com falha. Offset salvo para retomada.")
            break

        # Lista vazia = fim dos dados.
        if not dados:
            # # logger.info(f"[{origem}] Página {offset} vazia — fim dos registros. Total: {len(todos_registros)}")
            resetar_offset(tenant_id, origem, valor_padrao=valor_padrao_pagina)
            break

        # logger.info(f"[{origem}] Página {offset}: {len(dados)} registros recebidos.")

        for item in dados:
            filtrado = {campo: item.get(campo) for campo in campos_permitidos}
            if filtrado.get(chave_obrigatoria):
                todos_registros.append(filtrado)

        # Salva progresso e avança — se o processo morrer no meio, não perde a página atual.
        salvar_offset(tenant_id, origem, offset)
        time.sleep(sleep_request)
        offset += 1

    # logger.info(f"[{origem}] Extração finalizada | tenant={tenant_id} | registros={len(todos_registros)}")
    return todos_registros


def extrair_paginado_sem_filtro(
    url: str,
    headers: dict,
    origem: str,
    tenant_id: int,
    on_page,
    logger: logging.Logger,
    limit: int = 100,
    offset_inicial: int | None = None,
    extra_params: dict | None = None,
    timeout=(10, 120),
    sleep_request: float = 1.0,
    nome_param_pagina: str = "offset",
    nome_param_limite: str = "limit",
    valor_padrao_pagina: int = 1,
    max_tentativas: int = 5,
) -> dict:
    """
    Extrai página a página e entrega cada página ao on_page (que grava no banco).
    NADA é acumulado em memória: só contadores são mantidos.

    Mesmo contrato do extrair_paginado:
      - o parâmetro de página avança de 1 em 1 (NÃO de `limit` em `limit`);
      - rate limit / falha HTTP: offset salvo para retomada;
      - página vazia: offset resetado (próxima execução recomeça).
    """
    params_extra = extra_params.copy() if extra_params else {}
    offset = ler_offset(tenant_id, origem, offset_inicial, valor_padrao=valor_padrao_pagina)

    paginas = 0
    total_registros = 0
    status = "OK"
    mensagem = None

    while True:
        params = {nome_param_limite: limit, nome_param_pagina: offset, **params_extra}

        try:
            dados = _fetch_page(
                url, headers, params, timeout, offset,
                tenant_id, origem, logger, max_tentativas,
            )
        except RateLimitAtingido as exc:
            status = "RATE_LIMIT"
            mensagem = str(exc)
            break

        if dados is None:
            status = "ERRO"
            mensagem = f"Falha ao buscar a página {offset}. Offset salvo para retomada."
            break

        # Lista vazia = fim dos dados.
        if not dados:
            resetar_offset(tenant_id, origem, valor_padrao=valor_padrao_pagina)
            break

        # defesa: só dicts seguem para o repository
        itens = [i for i in dados if isinstance(i, dict)]
        qtd = len(itens)

        # Se `recebidos` vier muito acima de `limit`, a API está ignorando
        # o limite e devolvendo tudo de uma vez (causa clássica de estouro de RAM).
        logger.info("[%s] tenant=%s pagina=%s recebidos=%s", origem, tenant_id, offset, qtd)

        if itens:
            on_page(itens, offset, limit)

        # Salva progresso e avança — se o processo morrer, não perde a página atual.
        salvar_offset(tenant_id, origem, offset)

        paginas += 1
        total_registros += qtd
        offset += 1

        # solta a página antes de buscar a próxima
        del dados, itens
        if paginas % 20 == 0:
            gc.collect()

        time.sleep(sleep_request)

    return {
        "status": status,
        "mensagem": mensagem,
        "paginas": paginas,
        "registros": total_registros,
        "itens": total_registros,
        "total_registros": total_registros,
        "offset_final": offset,
    }


def _fetch_um(url, headers, timeout, codigo, tenant_id, origem, logger):
    """Busca um único registro por código. Retorna o dict de "dados", ou None se não existir/falhar."""
    response = None

    while True:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            # logger.info(f"[{origem}] GET {response.url} -> {response.status_code}")

            if response.status_code == 429:
                logger.warning(f"[{origem}] Rate limit atingido no código {codigo}. Salvando offset.")
                salvar_offset(tenant_id, origem, codigo)
                raise RateLimitAtingido(f"Rate limit atingido no código {codigo}")

            if response.status_code == 404:
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
        # logger.info(f"[{origem}] Código {codigo}: sucesso=false ({corpo.get('mensagemUsuarioFinal')}).")
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
    on_registro = None,
) -> list[dict]:

    codigo = ler_offset(tenant_id, origem, offset_inicial)

    todos_registros: list[dict] = []
    nao_encontrados_seguidos = 0

    for _ in range(quantidade_por_execucao):

        url = f"{url_base}?codigo_cliente={codigo}"

        try:
            item = _fetch_um(
                url,
                headers,
                timeout,
                codigo,
                tenant_id,
                origem,
                logger
            )

        except RateLimitAtingido:

            #logger.warning(
            #    f"[{origem}] Extração interrompida por rate limit no código {codigo}. "
            #    f"{len(todos_registros)} registros coletados nesta execução."
            #)

            break

        if item is None:

            nao_encontrados_seguidos += 1

            if nao_encontrados_seguidos >= max_nao_encontrados_seguidos:

                codigo += 1

                salvar_offset(
                    tenant_id,
                    origem,
                    codigo
                )

                break
        else:

            nao_encontrados_seguidos = 0

            filtrado = {campo: item.get(campo) for campo in campos_permitidos}

            todos_registros.append(filtrado)

            if on_registro:
                on_registro(filtrado, codigo)

        codigo += 1

        salvar_offset(
            tenant_id,
            origem,
            codigo
        )

        time.sleep(sleep_request)

    # logger.info(
    #    f"[{origem}] Extração finalizada | tenant={tenant_id} | "
    #    f"registros={len(todos_registros)} | próximo código={codigo}"
    #)
    return todos_registros