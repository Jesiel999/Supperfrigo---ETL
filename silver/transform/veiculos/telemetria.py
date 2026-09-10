from datetime import datetime
from core.logger import get_layer_logger
from repositories.econnect.telemetria_repository import buscar_raw_pendentes, marcar_processado
from repositories.sances.veiculo_repository import garantir_veiculo_stub  
from database.mysql_connection import connection_mysql

logger = get_layer_logger("silver", "telemetria_transform")


def _montar_bi(raw: dict, tenant_id: int) -> dict:
    return {
        "tenant_id": tenant_id,
        "codigo_raw": raw["id"],
        "dispositivo_id": raw.get("dispositivo_id"),
        "veiculo_id": raw["veiculo_id"],
        "data_evento": raw["data_evento"],
        "gsm_signal": raw.get("gsm_signal"),
        "data_mode": raw.get("data_mode"),
        "velocidade_kmh": raw.get("speed"),
        "velocidade_roda_kmh": raw.get("wheel_based_speed"),
        "tensao_externa_v": raw.get("external_voltage"),
        "tensao_bateria_v": raw.get("battery_voltage"),
        "corrente_bateria": raw.get("battery_current"),
        "gnss_status": raw.get("gnss_status"),
        "gnss_pdop": raw.get("gnss_pdop"),
        "gnss_hdop": raw.get("gnss_hdop"),
        "freio_acionado": raw.get("brake_switch"),
        "controle_cruzeiro_ativo": raw.get("cruise_control_active"),
        "embreagem_acionada": raw.get("clutch_switch"),
        "pto_estado": raw.get("pto_state"),
        "pedal_acelerador_pct": raw.get("acceleration_pedal_position"),
        "carga_motor_pct": raw.get("engine_current_load"),
        "combustivel_total_l": raw.get("engine_total_fuel_used"),
        "nivel_combustivel_pct": raw.get("fuel_level"),
        "rotacao_motor_rpm": raw.get("engine_speed"),
        "diagnosticos_suportados": raw.get("diagnostics_supported"),
        "requisicoes_suportadas": raw.get("requests_supported"),
        "indicacao_direcao": raw.get("direction_indication"),
        "desempenho_tacografo": raw.get("tachograph_performance"),
        "informacao_manuseio": raw.get("handling_info"),
        "evento_sistema": raw.get("system_event"),
        "temperatura_liquido_arrefecimento_c": raw.get("engine_coolant_temperature"),
        "taxa_combustivel_l_h": raw.get("fuel_rate"),
        "economia_instantanea": raw.get("instantaneous_fuel_economy"),
        "combustivel_total_alta_resolucao_l": raw.get("high_resolution_engine_total_fuel_used"),
        "modo_sleep": raw.get("sleep_mode"),
        "dados_validos": True,
        "data_processamento": datetime.now(),
    }


def _upsert_telemetria_bi(bi: dict) -> None:
    conn = connection_mysql()
    cursor = conn.cursor()
    try:
        colunas = list(bi.keys())
        placeholders = [f"%({c})s" for c in colunas]
        updates = [f"{c}=VALUES({c})" for c in colunas if c != "codigo_raw"]
        cursor.execute(
            f"""
            INSERT INTO telemetria_bi ({', '.join(colunas)})
            VALUES ({', '.join(placeholders)})
            ON DUPLICATE KEY UPDATE {', '.join(updates)}
            """,
            bi,
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def processar_telemetria_pendentes(
    tenant_id: int,
    pipeline: str,
    limite: int = 1000
 ) -> dict:
    pendentes = buscar_raw_pendentes(tenant_id, limite)
    if not pendentes:
        return {"processados": 0}

    ids_processados = []
    ids_com_erro = []

    for raw in pendentes:
        try:
            garantir_veiculo_stub(tenant_id=tenant_id, veiculo_id=raw["veiculo_id"])

            bi = _montar_bi(raw, tenant_id)
            _upsert_telemetria_bi(bi)
            ids_processados.append(raw["id"])
        except Exception as e:
            ids_com_erro.append(raw["id"])
            logger.error(f"Erro ao processar telemetria_raw id={raw['id']}: {e}")

    marcar_processado(ids_processados)

    # logger.info(
    #    f"[SILVER telemetria] tenant={tenant_id} | "
    #    f"processados={len(ids_processados)} | erros={len(ids_com_erro)}"
    #)
    return {"processados": len(ids_processados), "erros": len(ids_com_erro)}