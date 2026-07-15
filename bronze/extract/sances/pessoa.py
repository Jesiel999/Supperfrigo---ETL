import requests
import time
import os
import logging

from requests.exceptions import ConnectionError, Timeout, RequestException
from datetime import datetime

from config.settings import (
    SANCES_TOKEN,
    URL_FINANCEIRO,
    REQUEST_TIMEOUT,
    RATE_LIMIT_SLEEP,
    SLEEP_REQUEST,
)
from core.logger import get_layer_logger

class RateLimitAtingido(Exception):
    """Exceção utilizada para encerrar a extração quando atingir rate limit."""
    pass
    
logger = get_layer_logger("bronze", "pessoa_sances")

HEADERS = {"Authorization": f"Bearer {SANCES_TOKEN}"}

# ==========================================
# CAMPOS PERMITIDOS
# ==========================================
CAMPOS_PERMITIDOS = [
    
]

CAMPOS_DATA = [
]

# ==========================================
# ARQUIVO DE CONTROLE DE OFFSET
# Guarda a página atual da extração.
# Resetado para 1 ao terminar com sucesso.
# Mantido no valor atual ao falhar, para
# retomar da página onde parou.
# ==========================================
OFFSET_FILE = "logs/bronze/pessoa_codigo.txt"


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
    """Converte datas e filtra apenas campos permitidos."""
    for campo in CAMPOS_DATA:
        if campo in item and item[campo]:
            item[campo] = _converter_data(item[campo])
    return {k: v for k, v in item.items() if k in CAMPOS_PERMITIDOS}


def _salvar_offset(offset: int, offset_file: str):
    """Persiste o offset atual em disco."""
    os.makedirs("logs/bronze", exist_ok=True)
    with open(offset_file, "w") as f:
        f.write(str(offset))


def _resetar_offset():
    """
    Reseta o offset para 1 após conclusão bem-sucedida.
    Na próxima execução a varredura começa do início.
    """
    _salvar_offset(1)
    logger.info("Offset resetado para 1. Próxima execução varre do início.")


def _ler_offset(offset_inicial: int | None) -> int:
    """
    Retorna o offset de onde a extração deve começar.
    Prioridade:
      1. offset_inicial passado por parâmetro (ex: forçar início manual)
      2. Offset salvo em disco (retomar de onde parou após falha)
      3. 1 (padrão — primeira execução)
    """
    if offset_inicial is not None:
        logger.info(f"Offset forçado por parâmetro: {offset_inicial}")
        return offset_inicial

    if os.path.exists(offset_file):
        with open(offset_file) as f:
            valor = f.read().strip()
        if valor.isdigit():
            offset = int(valor)
            logger.info(f"Offset recuperado do disco: {offset}")
            return offset

    logger.info("Nenhum offset salvo. Iniciando do offset 1.")
    return 1


def _fetch_page(
    limit: int,
    offset: int,
    extra_params: dict | None = None,
    offset_file: str | None = None,
) -> list[dict] | None:
    """
    Busca uma página da API.

    Returns:
        list[dict]  — registros da página (pode ser lista vazia = fim dos dados)
        None        — falha definitiva (erro HTTP não recuperável)
    """
    params = {"limit": limit, "offset": offset}
    if extra_params:
        params.update(extra_params)

    response = None

    while True:
        try:
            response = requests.get(
                URL_FINANCEIRO,
                headers=HEADERS,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            logger.info(f"GET {response.url} -> {response.status_code}")

            # ==========================================
            # RATE LIMIT — aguarda e tenta de novo
            # ==========================================
            if response.status_code == 429:
                logger.warning(
                    f"Rate limit atingido na página {offset}. "
                    f"Encerrando Bronze e salvando offset para continuação futura."
                )

                _salvar_offset(offset)

                raise RateLimitAtingido(
                    f"Rate limit atingido na página {offset}"
                )

            if response.status_code == 200:
                break

            # ==========================================
            # ERRO HTTP DEFINITIVO
            # ==========================================
            logger.error(
                f"Erro HTTP {response.status_code} na página {offset}: "
                f"{response.text[:300]}"
            )
            _salvar_offset(offset)  # guarda para retomar depois
            return None

        except Timeout:
            logger.warning(f"Timeout na página {offset}. Aguardando 5s e tentando de novo...")
            time.sleep(5)

        except ConnectionError:
            logger.warning(f"Erro de conexão na página {offset}. Aguardando 5s...")
            time.sleep(5)

        except RequestException as e:
            logger.error(f"Erro de request inesperado na página {offset}: {e}")
            time.sleep(5)

    try:
        dados = response.json().get("dados", [])
        return dados
    except Exception as e:
        logger.error(f"Erro ao parsear JSON da página {offset}: {e}")
        _salvar_offset(offset)
        return None


# ==========================================
# INTERFACE PÚBLICA
# ==========================================

def extrair_financeiro(
    limit: int = 100,
    offset_inicial: int | None = None,
    extra_params: dict | None = None,
    data_baixa_inicial: str | None = None,
    data_baixa_final: str | None = None,
    data_insercao_inicial: str | None = None,
    data_insercao_final: str | None = None,
) -> list[dict]:
   
    os.makedirs("logs/bronze", exist_ok=True)

    # ==========================================
    # MONTA PARÂMETROS DE FILTRO
    # ==========================================
    params_extra: dict = extra_params.copy() if extra_params else {}

    if data_baixa_inicial:
        params_extra["data_baixa_inicial"] = data_baixa_inicial
        logger.info(f"Filtro data_baixa_inicial: {data_baixa_inicial}")

    if data_baixa_final:
        params_extra["data_baixa_final"] = data_baixa_final
        logger.info(f"Filtro data_baixa_final: {data_baixa_final}")

    if data_insercao_inicial:
        params_extra["data_insercao_inicial"] = data_insercao_inicial
        logger.info(f"Filtro data_insercao_inicial: {data_insercao_inicial}")
    
    if data_insercao_final:
        params_extra["data_insercao_final"] = data_insercao_final
        logger.info(f"Filtro data_insercao_final: {data_insercao_final}")

    # ==========================================
    # DETERMINA OFFSET DE INÍCIO
    # ==========================================
    offset = _ler_offset(offset_inicial)

    todos_registros: list[dict] = []
    extracao_ok = False  # flag: True apenas se terminou naturalmente (sem erro)

    # ==========================================
    # LOOP DE PAGINAÇÃO
    # ==========================================
    while True:

        # ==========================================
        # FALHA DEFINITIVA NA API
        # Offset já foi salvo dentro de _fetch_page.
        # Retoma da mesma página na próxima execução.
        # ==========================================

        try:
            dados = _fetch_page(
                limit,
                offset,
                params_extra if params_extra else None
            )

        except RateLimitAtingido:
            logger.warning(
                f"Extração interrompida por rate limit. "
                f"Retornando {len(todos_registros)} registros já coletados."
            )

            extracao_ok = True
            break

        # ==========================================
        # FIM DOS DADOS
        # API retornou lista vazia = não há mais páginas.
        # Marca extração como bem-sucedida.
        # ==========================================
        if not dados:
            logger.info(
                f"Página {offset} veio vazia — fim dos registros. "
                f"Total extraído: {len(todos_registros)} registros."
            )
            extracao_ok = True
            break

        logger.info(f"Página {offset}: {len(dados)} registros recebidos.")

        # ==========================================
        # PROCESSA REGISTROS DA PÁGINA
        # ==========================================
        for item in dados:
            filtrado = _filtrar_item(item)
            if filtrado.get("codigo"):
                todos_registros.append(filtrado)

        # ==========================================
        # SALVA PROGRESSO E AVANÇA
        # Garante que, se o processo morrer durante
        # o processamento, não perde a página atual.
        # ==========================================
        _salvar_offset(offset)
        time.sleep(SLEEP_REQUEST)
        offset += 1

    # ==========================================
    # PÓS-LOOP: RESETA OU MANTÉM OFFSET
    # ==========================================
    if extracao_ok:
        _resetar_offset()
    else:
        logger.warning(
            "Extração encerrada com falha. "
            "Execute novamente para retomar do ponto de parada."
        )

    logger.info(f"Extração finalizada | registros={len(todos_registros)} | sucesso={extracao_ok}")
    return todos_registros