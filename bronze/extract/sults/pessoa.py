from config.settings import URL_SULTS_PESSOA, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_paginado_sem_filtro
from repositories.pessoa_repository import upsert_pessoa_sults_completo

logger = get_layer_logger("bronze", "pessoa_sults")

ORIGEM = "pessoa_sults"

CAMPOS_PERMITIDOS = [
    "id", "nome", "ativo", "sexo", "cpf",
    "celular", "telefone", "email",
    "dtCadastro", "dtUltimaAlteracao", "dtInativacao",
    "endereco",
    "empresa",
    "campoAdicional",
]


def _filtrar_item(item: dict) -> dict:
    return {campo: item.get(campo) for campo in CAMPOS_PERMITIDOS}


def extrair_pessoa_sults(
    tenant_id: int,
    token: str,
    limit: int = 100,
    offset_inicial: int | None = None,
) -> dict:
    headers = {"Authorization": token}

    def _persistir_pagina(itens: list[dict], offset: int, limit_usado: int) -> None:
        filtrados = []
        for it in itens:
            f = _filtrar_item(it)
            if f.get("id"):
                filtrados.append(f)
        # upsert_pessoa_sults_completo já sabe distribuir entre
        # pessoa_sults_raw + endereco_sults_raw + empresa_sults_raw +
        # campoAdicional_sults_raw — reaproveitado sem alteração.
        upsert_pessoa_sults_completo(filtrados)

    return extrair_paginado_sem_filtro(
        url=URL_SULTS_PESSOA,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        on_page=_persistir_pagina,
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
        nome_param_pagina="start",
        valor_padrao_pagina=0,
    )