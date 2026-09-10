import requests
import time
from datetime import datetime

from requests.exceptions import ConnectionError, Timeout, RequestException

from config.settings import URL_ECONNECT_TELEMETRIA, REQUEST_TIMEOUT
from core.logger import get_layer_logger
from repositories.offset_repository import marcar_inicio_execucao

logger = get_layer_logger("bronze", "telemetria_econnect")

ORIGEM = "telemetria_econnect"


class RateLimitAtingido(Exception):
    pass


def _converter_data(valor) -> datetime | None:
    """gps_timestamp vem como 'YYYY-MM-DD HH:MM:SS' (sem timezone explícito)."""
    if not valor:
        return None

    try:
        return datetime.strptime(
            str(valor).strip(), 
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception as e:
        # logger.error(f"Erro ao converter data_evento={valor}: {e}")
        return None


def _mapear_log(equipamento_id, log: dict) -> dict:

    return {
        "veiculo_id": equipamento_id,
        "dispositivo_id": str(log.get("rastreador_esn")) if log.get("rastreador_esn") is not None else None,
        "data_evento": _converter_data(log.get("gps_timestamp")),
        "gsm_signal": log.get("gsm_rssi"),
        "data_mode": None,  
        "speed": log.get("gps_speed"),
        "external_voltage": None, 
        "battery_voltage": log.get("bateria_volt"),
        "battery_current": None,
        "gnss_status": bool(log.get("gps_fixo")) if log.get("gps_fixo") is not None else None,
        "brake_switch": log.get("fms_brake_switch"),
        "wheel_based_speed": log.get("fms_wheel_based_speed"),
        "cruise_control_active": log.get("fms_cruise_control_active"),
        "clutch_switch": log.get("fms_clutch_switch"),
        "pto_state": log.get("fms_pto_state"),
        "acceleration_pedal_position": log.get("fms_acceleration_pedal_position"),
        "engine_current_load": log.get("fms_engine_current_load"),
        "engine_total_fuel_used": log.get("fms_engine_total_fuel_used"),
        "fuel_level": log.get("fms_fuel_level"),
        "engine_speed": log.get("fms_engine_speed"),
        "diagnostics_supported": log.get("fms_diagnostics_supported"),
        "requests_supported": log.get("fms_requests_supported"),
        "direction_indication": log.get("fms_direction_indication"),
        "tachograph_performance": log.get("fms_tachograph_performance"),
        "handling_info": log.get("fms_handling_info"),
        "system_event": log.get("fms_system_event"),
        "engine_coolant_temperature": log.get("fms_engine_coolant_temperature"),
        "fuel_rate": log.get("fms_fuel_rate"),
        "instantaneous_fuel_economy": log.get("fms_instantaneous_fuel_economy"),
        "high_resolution_engine_total_fuel_used": log.get("fms_high_resolution_engine_total_fuel_used"),
        "gnss_pdop": None,
        "gnss_hdop": None,  
        "sleep_mode": None,
    }


def _fetch(
    tenant_id: int,
    endpoint: str,
    offset_inicial: int | None = None,
) -> list[dict] | None:

    response = None

    while True:
        try:

            params = {}

            if offset_inicial is not None:
                params["offset"] = offset_inicial

            response = requests.get(
                endpoint,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            logger.info(
                f"[{ORIGEM}] "
                f"tenant={tenant_id} | "
                f"GET {response.url} -> "
                f"{response.status_code}"
            )

            if response.status_code == 429:
                logger.warning(
                    f"[{ORIGEM}] "
                    f"Rate limit atingido."
                )

                raise RateLimitAtingido(
                    "Rate limit atingido"
                )

            if response.status_code == 200:
                break

            logger.error(
                f"[{ORIGEM}] "
                f"Erro HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )

            return None

        except Timeout:
            logger.warning(
                f"[{ORIGEM}] "
                f"Timeout. Aguardando 5s..."
            )
            time.sleep(5)

        except ConnectionError:
            logger.warning(
                f"[{ORIGEM}] "
                f"Erro de conexão. Aguardando 5s..."
            )
            time.sleep(5)

        except RequestException as e:
            logger.error(
                f"[{ORIGEM}] "
                f"Erro de request: {e}"
            )
            time.sleep(5)

    try:
        corpo = response.json()

    except Exception as e:
        logger.error(
            f"[{ORIGEM}] "
            f"Erro ao parsear JSON: {e}"
        )
        return None

    if not isinstance(corpo, list):
        # logger.error(
        #    f"[{ORIGEM}] "
        #    f"Formato de resposta inesperado: "
        #    f"{type(corpo)}"
        #)
        return None

    return corpo



def extrair_telemetria_econnect(
    tenant_id: int,
    endpoint: str,
    offset_inicial: int | None = None,
) -> dict:

    # logger.info(
    #    f"[{ORIGEM}] "
    #    f"Iniciando extração | "
    #    f"tenant={tenant_id} | "
    #    f"offset_inicial={offset_inicial}"
    #)

    try:

        itens = _fetch(
            tenant_id=tenant_id,
            endpoint=endpoint,
            offset_inicial=offset_inicial,
        )

    except RateLimitAtingido:

        return {
            "registros": [],
            "status": "RATE_LIMIT",
            "offset_inicial": offset_inicial,
        }

    if itens is None:

        return {
            "registros": [],
            "status": "ERRO",
            "offset_inicial": offset_inicial,
        }

    registros = []
    ignorados_sem_log = 0

    for item in itens:

        equipamento_id = item.get("equipamentoId")

        log = item.get(
            "logs_telemetria_refrigeracao"
        )

        if not equipamento_id or not log:

            ignorados_sem_log += 1
            continue

        registros.append(
            _mapear_log(
                equipamento_id,
                log
            )
        )

    # logger.info(
    #    f"[{ORIGEM}] "
    #    f"tenant={tenant_id} | "
    #    f"{len(registros)} registros mapeados | "
    #    f"{ignorados_sem_log} equipamentos "
    #    f"sem log"
    #)

    return {
        "registros": registros,
        "status": "CONCLUIDO",
        "offset_inicial": offset_inicial,
    }