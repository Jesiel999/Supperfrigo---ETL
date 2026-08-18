from config.settings import SANCES_TOKEN, URL_SANCES_ESTOQUE, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_paginado_estoque
from repositories.sances.estoque_repository import salvar_pagina_raw

logger = get_layer_logger("bronze", "estoque_sances")

ORIGEM = "estoque_sances"

FILTROS_DEFAULT = {"ativo": 1}


def extrair_estoque_sances(
    tenant_id: int,
    token: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {token or SANCES_TOKEN}"}
    extra_params = {**FILTROS_DEFAULT, **(filtros or {})}

    def _persistir_pagina(itens: list[dict], offset: int, limit_usado: int) -> None:
        salvar_pagina_raw(
            tenant_id=tenant_id,
            pipeline=ORIGEM,
            offset_pagina=offset,
            itens=itens,
        )

    return extrair_paginado_estoque(
        url=URL_SANCES_ESTOQUE,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        on_page=_persistir_pagina,
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        extra_params=extra_params,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
    )
