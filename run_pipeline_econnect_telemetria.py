# run_pipeline_econnect_telemetria.py
from config.logging import setup_logging
from pipelines.telemetria_pipeline import executar_pipeline_telemetria

setup_logging()

def executar_econnect_telemetria():
    return executar_pipeline_telemetria(tenant_id=3)

if __name__ == "__main__":
    print(executar_econnect_telemetria())