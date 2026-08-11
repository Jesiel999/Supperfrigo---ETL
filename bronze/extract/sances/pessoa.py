from config.settings import SANCES_TOKEN, URL_SANCES_PESSOA, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_por_codigo

logger = get_layer_logger("bronze", "pessoa_sances")

ORIGEM = "pessoa_sances"

CAMPOS_PERMITIDOS = [
    "codigo_cliente", "tipo",
    "cpf_cnpj", "nome_cliente",
    "sexo",
    "endereco", 
    "email",     
    "telefone",
]

def extrair_pessoa_sances(
    tenant_id: int,
    token: str | None = None,
    offset_inicial: int | None = None,
    quantidade_por_execucao: int = 5000,
) -> list[dict]:

    headers = {"Authorization": f"Bearer {'token' or 'SANCES_TOKEN'}"}

    return extrair_por_codigo(
        url_base=URL_SANCES_PESSOA,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        campos_permitidos=CAMPOS_PERMITIDOS,
        logger=logger,
        offset_inicial=offset_inicial,
        quantidade_por_execucao=quantidade_por_execucao,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
    )
