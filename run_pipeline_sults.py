from config.logging import setup_logging
from datetime import datetime
from pipelines.chamados_sults_pipeline import executar_pipeline_chamados

setup_logging()

def executar_sults_chamados():

    return executar_pipeline_chamados(
        tenant_id=2
    )

if __name__ == "__main__":
    print(executar_sults_chamados())