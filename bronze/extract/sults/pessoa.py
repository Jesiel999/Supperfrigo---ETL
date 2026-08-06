from config.settings import URL_PESSOA_SULTS, REQUEST_TIMEOUT, SLEEP_REQUEST
from core.logger import get_layer_logger
from bronze.extract._base import extrair_paginado

logger = get_layer_logger("bronze", "pessoa_sults")

ORIGEM = "pessoa_sults"

CAMPOS_PERMITIDOS = [
    "id", "nome", "ativo", "sexo", "cpf",
    "celular", "telefone", "email",  
    "dtCadastro", "dtUltimaAlteracao", "dtInativacao",
    "endereco",      
    "empresa",        
]


def extrair_pessoa_sults(
    tenant_id: int,
    token: str,
    limit: int = 100,
    offset_inicial: int | None = None,
) -> list[dict]:
    headers = {"Authorization": token}

    return extrair_paginado(
        url=URL_PESSOA_SULTS,
        headers=headers,
        origem=ORIGEM,
        tenant_id=tenant_id,
        campos_permitidos=CAMPOS_PERMITIDOS,
        chave_obrigatoria="id",
        logger=logger,
        limit=limit,
        offset_inicial=offset_inicial,
        timeout=REQUEST_TIMEOUT,
        sleep_request=SLEEP_REQUEST,
        nome_param_pagina="start",
        valor_padrao_pagina=0,
    )

