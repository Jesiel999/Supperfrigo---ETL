import logging
from core.logger import get_layer_logger

logger = get_layer_logger("silver", "pessoa_transform")

def transformar_pessoa(registros_raw: list[dict]) -> list[dict]:
    """
    Retorna dimensão pessoa_bi (única).
    """

    pessoas_map: dict[int, dict] = {}

    for raw in registros_raw:
        try:
            codigo_pessoa = raw.get("codigo_pessoa")

            if codigo_pessoa is not None and codigo_pessoa not in pessoas_map:
                pessoas_map[codigo_pessoa] = {
                    "codigo_pessoa": codigo_pessoa,
                    "nome_pessoa": raw.get("nome_pessoa")
                }

        except Exception as e:
            logger.error(f"Erro ao transformar pessoa {raw.get('codigo')}: {e}")

    resultado = list(pessoas_map.values())

    logger.info(f"Silver pessoa: {len(resultado)} registros únicos.")
    return resultado