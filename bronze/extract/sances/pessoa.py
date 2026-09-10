from config.settings import SANCES_TOKEN, URL_SANCES_PESSOA, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_por_codigo
from repositories.pessoa_repository import upsert_pessoa_sances_completo

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


def _filtrar_item(item: dict) -> dict:
    return {campo: item.get(campo) for campo in CAMPOS_PERMITIDOS}


def extrair_pessoa_sances(
    tenant_id: int,
    token: str | None = None,
    offset_inicial: int | None = None,
    quantidade_por_execucao: int = 5000,
) -> dict:
    headers = {"Authorization": f"Bearer {token or 'SANCES_TOKEN'}"}

    headers = {"Authorization": f"Bearer {'token' or 'SANCES_TOKEN'}"}
    def _persistir_registro(item: dict, codigo: int) -> None:
        filtrado = _filtrar_item(item)
        if not filtrado.get("codigo_cliente"):
            return
        # upsert_pessoa_sances_completo já sabe distribuir entre
        # pessoa_sances_raw + endereco_sances_raw + email_sances_raw +
        # telefone_sances_raw — reaproveitado sem alteração.
        upsert_pessoa_sances_completo([filtrado])

    return extrair_por_codigo(
        url_base=URL_SANCES_PESSOA,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        campos_permitidos=CAMPOS_PERMITIDOS,
        on_registro=_persistir_registro,
        logger=logger,
        offset_inicial=offset_inicial,
        quantidade_por_execucao=quantidade_por_execucao,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
    )