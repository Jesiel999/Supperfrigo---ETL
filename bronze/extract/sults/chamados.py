import requests
import time
import os

from requests.exceptions import ConnectionError, Timeout, RequestException

from config.settings import (
    SULTS_TOKEN,
    URL_CHAMADOS,
    REQUEST_TIMEOUT,
    SLEEP_REQUEST,
)
from core.logger import get_layer_logger
from repositories.sults.chamados_repository import upsert_chamados_raw
from repositories.sults.chamados_apoio_repository import upsert_chamados_apoio_raw
from repositories.sults.chamados_etiqueta_repository import upsert_chamados_etiqueta_raw


class RateLimitAtingido(Exception):
    """Exceção utilizada para encerrar a extração quando atingir rate limit."""
    pass


logger = get_layer_logger("bronze", "chamados")

HEADERS = {"Authorization": f"{SULTS_TOKEN}"}
start_FILE = "logs/bronze/chamados_start.txt"


# ==========================================
# HELPERS
# ==========================================

def _salvar_start(start: int):
    """Persiste o start atual em disco."""
    os.makedirs("logs/bronze", exist_ok=True)
    with open(start_FILE, "w") as f:
        f.write(str(start))


def _resetar_start():
    """Reseta o start para 1 após conclusão bem-sucedida."""
    _salvar_start(1)
    logger.info("start resetado para 1. Próxima execução varre do início.")


def _ler_start(start_inicial: int | None) -> int:
    """Retorna o start de onde a extração deve começar."""
    if start_inicial is not None:
        logger.info(f"start forçado por parâmetro: {start_inicial}")
        return start_inicial

    if os.path.exists(start_FILE):
        with open(start_FILE) as f:
            valor = f.read().strip()
        if valor.isdigit():
            start = int(valor)
            logger.info(f"start recuperado do disco: {start}")
            return start

    logger.info("Nenhum start salvo. Iniciando do start 1.")
    return 1


def _fetch_page(
    limit: int,
    start: int,
    extra_params: dict | None = None,
) -> tuple[list[dict] | None, int]:
    """
    Busca uma página da API.

    Returns:
        (dados, total_pages)
        dados=None  -> falha definitiva (erro HTTP/parse não recuperável)
        dados=[]    -> fim natural da paginação
    """
    params = { "start": start, "limit": limit }
    if extra_params:
        params.update(extra_params)

    response = None

    while True:
        try:
            response = requests.get(
                URL_CHAMADOS,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            logger.info(f"GET {response.url} -> {response.status_code}")

            if response.status_code == 429:
                logger.warning(
                    f"Rate limit atingido na página {start}. "
                    f"Encerrando Bronze e salvando start para continuação futura."
                )
                _salvar_start(start)
                raise RateLimitAtingido(f"Rate limit atingido na página {start}")

            if response.status_code == 200:
                break

            logger.error(
                f"Erro HTTP {response.status_code} na página {start}: "
                f"{response.text[:300]}"
            )
            _salvar_start(start)
            return None, 0

        except Timeout:
            logger.warning(f"Timeout na página {start}. Aguardando 5s e tentando de novo...")
            time.sleep(5)

        except ConnectionError:
            logger.warning(f"Erro de conexão na página {start}. Aguardando 5s...")
            time.sleep(5)

        except RequestException as e:
            logger.error(f"Erro de request inesperado na página {start}: {e}")
            time.sleep(5)

    try:
        body = response.json()
        dados = body.get("data", []) or []
        total_pages = body.get("totalPage", 1) or 1
        return dados, int(total_pages)
    except Exception as e:
        logger.error(f"Erro ao parsear JSON da página {start}: {e}")
        _salvar_start(start)
        return None, 0


# ==========================================
# INTERFACE PÚBLICA
# ==========================================

def extrair_chamados(
    tenant_id: int,
    limit: int = 100,
    start_inicial: int | None = None,
    extra_params: dict | None = None,
    aberto: str | None = None,
) -> dict:
    """
    Extrai chamados da API, acumula todas as páginas e grava em raw.
    """

    os.makedirs("logs/bronze", exist_ok=True)

    params_extra: dict = extra_params.copy() if extra_params else {}
    if aberto:
        params_extra["aberto"] = aberto
        logger.info(f"Filtro aberto: {aberto}")

    start = _ler_start(start_inicial)

    chamados_raw: list[dict] = []
    apoios_raw: list[dict] = []
    etiquetas_raw: list[dict] = []
    codigos_vistos = set()
    codigos_repetidos = {}
    pagina_atual = 1

    extracao_ok = False

    while True:
        try:
            dados, total_pages = _fetch_page(
                limit=limit,
                start=start,
                extra_params=params_extra if params_extra else None,
            )

        except RateLimitAtingido:
            logger.warning(
                f"Extração interrompida por rate limit. "
                f"Retornando {len(chamados_raw)} chamados já coletados."
            )
            extracao_ok = True
            break

        if dados is None:
            logger.error(f"Falha definitiva na página {start}. Interrompendo extração.")
            extracao_ok = False
            break

        # Fim natural: página vazia
        if not dados:
            logger.info(
                f"[EXTRACT] Página {start} vazia. "
                f"Fim da paginação tenant={tenant_id} | "
                f"Chamados acumulados={len(chamados_raw)}"
            )
            extracao_ok = True
            break

        logger.info(
            f"[EXTRACT] tenant={tenant_id} página={start}/{total_pages} "
            f"registros={len(dados)}"
        )

        # ==========================================
        # PROCESSA E ACUMULA A PÁGINA ATUAL
        # ==========================================
        for chamado in dados:
            try:
                codigo = chamado.get("id")
                if not codigo:
                    logger.warning("Chamado sem ID encontrado — ignorado")
                    continue

                # diagnóstico de duplicidade 
                if codigo in codigos_vistos: 
                    codigos_repetidos[codigo] = codigos_repetidos.get(codigo, 0) + 1 
                else: 
                    codigos_vistos.add(codigo)

                solicitante = chamado.get("solicitante") or {}
                responsavel = chamado.get("responsavel") or {}
                unidade = chamado.get("unidade") or {}
                departamento = chamado.get("departamento") or {}
                departamento_envio = chamado.get("departamentoEnvio") or {}
                assunto = chamado.get("assunto") or {}

                chamado_raw = {
                    "tenant_id": tenant_id,
                    "codigo": codigo,
                    "titulo": chamado.get("titulo"),
                    "solicitante_id": solicitante.get("id"),
                    "solicitante_nome": solicitante.get("nome"),
                    "responsavel_id": responsavel.get("id"),
                    "responsavel_nome": responsavel.get("nome"),
                    "unidade_id": unidade.get("id"),
                    "unidade_nome": unidade.get("nome"),
                    "departamento_id": departamento.get("id"),
                    "departamento_nome": departamento.get("nome"),
                    "departamento_envio_id": departamento_envio.get("id"),
                    "departamento_envio_nome": departamento_envio.get("nome"),
                    "assunto_id": assunto.get("id"),
                    "assunto_nome": assunto.get("nome"),
                    "tipo": chamado.get("tipo"),
                    "situacao": chamado.get("situacao"),
                    "data_aberto": chamado.get("aberto"),
                    "data_resolvido": chamado.get("resolvido"),
                    "data_concluido": chamado.get("concluido"),
                    "data_resolver_planejado": chamado.get("resolverPlanejado"),
                    "data_resolver_estipulado": chamado.get("resolverEstipulado"),
                    "data_primeira_interacao": chamado.get("primeiraInteracao"),
                    "data_ultima_alteracao": chamado.get("ultimaAlteracao"),
                    "avaliacao_nota": chamado.get("avaliacaoNota"),
                    "avaliacao_observacao": chamado.get("avaliacaoObservacao"),
                    "quantidade_interacao_publico": chamado.get("countInteracaoPublico"),
                    "quantidade_interacao_interno": chamado.get("countInteracaoInterno"),
                }
                chamados_raw.append(chamado_raw)

                # APOIOS
                apoios = chamado.get("apoio") or []
                for apoio in apoios:
                    try:
                        pessoa = apoio.get("pessapoiooa") or apoio.get("pessoa") or {}
                        departamento_apoio = apoio.get("departamento") or {}

                        apoio_raw = {
                            "tenant_id": tenant_id,
                            "chamado_codigo": codigo,
                            "pessoa_id": pessoa.get("id"),
                            "pessoa_nome": pessoa.get("nome"),
                            "departamento_id": departamento_apoio.get("id"),
                            "departamento_nome": departamento_apoio.get("nome"),
                            "pessoa_unidade": apoio.get("pessoaUnidade", False),
                        }
                        apoios_raw.append(apoio_raw)
                    except Exception as e:
                        logger.error(f"Erro ao extrair apoio do chamado {codigo}: {e}")

                # ETIQUETAS
                etiquetas = chamado.get("etiqueta") or []
                for etiqueta in etiquetas:
                    try:
                        etiqueta_raw = {
                            "tenant_id": tenant_id,
                            "chamado_codigo": codigo,
                            "etiqueta_id": etiqueta.get("id"),
                            "etiqueta_nome": etiqueta.get("nome"),
                            "etiqueta_cor": etiqueta.get("cor"),
                        }
                        etiquetas_raw.append(etiqueta_raw)
                    except Exception as e:
                        logger.error(f"Erro ao extrair etiqueta do chamado {codigo}: {e}")

            except Exception as e:
                logger.error(f"Erro ao processar chamado {chamado.get('id')}: {e}")

        # salva o próximo start a ser retomado
        proximo_start = start + 1
        _salvar_start(proximo_start)

        # se esta foi a última página, encerra APÓS processar/acumular
        if start >= 16000:
            logger.info(
                f"[EXTRACT] Último lote processado tenant={tenant_id} "
                f"(start={start}). "
                f"Chamados acumulados={len(chamados_raw)}"
            )
            extracao_ok = True
            break

        start = proximo_start
        time.sleep(SLEEP_REQUEST)
        
    logger.info(f"Total acumulado em memória: {len(chamados_raw)}")
    logger.info(f"Códigos únicos em memória: {len(codigos_vistos)}")
    logger.info(f"Códigos repetidos em memória: {len(codigos_repetidos)}")

    if codigos_repetidos:
        top = list(codigos_repetidos.items())[:20]
        logger.warning(f"Exemplos de códigos repetidos: {top}")
    # ==========================================
    # UPSERT NO RAW
    # ==========================================
    logger.info(f"Carregando {len(chamados_raw)} chamados na tabela raw")
    resultado_chamados = upsert_chamados_raw(chamados_raw)

    logger.info(f"Carregando {len(apoios_raw)} apoios na tabela raw")
    resultado_apoios = upsert_chamados_apoio_raw(apoios_raw)

    logger.info(f"Carregando {len(etiquetas_raw)} etiquetas na tabela raw")
    resultado_etiquetas = upsert_chamados_etiqueta_raw(etiquetas_raw)

    if extracao_ok:
        _resetar_start()
    else:
        logger.warning(
            "Extração encerrada com falha. "
            "Execute novamente para retomar do ponto de parada."
        )

    logger.info(
        f"Bronze Extract concluído | "
        f"Chamados acumulados={len(chamados_raw)} | "
        f"Apoios acumulados={len(apoios_raw)} | "
        f"Etiquetas acumuladas={len(etiquetas_raw)} | "
        f"Upsert chamados={resultado_chamados} | "
        f"Upsert apoios={resultado_apoios} | "
        f"Upsert etiquetas={resultado_etiquetas}"
    )

    return {
        "chamados": chamados_raw,
        "apoios": apoios_raw,
        "etiquetas": etiquetas_raw,
        "resultado_upsert": {
            "chamados": resultado_chamados,
            "apoios": resultado_apoios,
            "etiquetas": resultado_etiquetas,
        },
    }
