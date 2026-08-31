from config.settings import SANCES_TOKEN, URL_SANCES_POS_VENDA, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_paginado_estoque
from repositories.sances.pos_venda_repository import salvar_pagina_raw

logger = get_layer_logger("bronze", "pos_venda_sances")

ORIGEM = "pos_venda_sances"


def extrair_pos_venda_sances(
    tenant_id: int,
    token: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
) -> dict:
    """
    Extrai pós-vendas paginando. Cada item da página já vem com
    pecas/servicos/notas/parcelas aninhados — tudo é persistido em
    salvar_pagina_raw numa única transação por página.
    """
    headers = {"Authorization": f"Bearer {token or SANCES_TOKEN}"}
    extra_params = filtros or {}

    def _persistir_pagina(itens: list[dict], offset: int, limit_usado: int) -> None:
        salvar_pagina_raw(
            tenant_id=tenant_id,
            offset_pagina=offset,
            itens=itens,
        )

    return extrair_paginado_estoque(
        url=URL_SANCES_POS_VENDA,
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