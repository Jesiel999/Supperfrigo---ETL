from datetime import date
import logging
from core.logger import get_layer_logger

logger = get_layer_logger("silver", "empresa_transform")

def transformar_empresa(registros_raw: list[dict]) -> list[dict]:
    """
    Retorna dimensão empresa_bi (única).
    """

    empresas_map: dict[int, dict] = {}

    for raw in registros_raw:
        try:
            codigo_empresa = raw.get("codigo_empresa")

            if codigo_empresa is not None and codigo_empresa not in empresas_map:
                empresas_map[codigo_empresa] = {
                    "codigo_empresa": codigo_empresa,
                    "nome_empresa": raw.get("nome_empresa")
                }

        except Exception as e:
            logger.error(f"Erro ao transformar empresa {raw.get('codigo')}: {e}")

    resultado = list(empresas_map.values())

    logger.info(f"Silver empresa: {len(resultado)} registros únicos.")
    return resultado
   