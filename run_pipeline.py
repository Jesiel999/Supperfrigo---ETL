from config.logging import setup_logging
from datetime import datetime
from pipelines.financeiro_pipeline import executar_pipeline_financeiro

setup_logging()

if __name__ == "__main__":
    resultado = executar_pipeline_financeiro(
        tenant_id = 1, 
        data_baixa_inicial="2026-05-01",
        data_baixa_final="2026-06-30",
        data_vencimento_inicial="",
        data_vencimento_final="",

        # data_vencimento_final=datetime.now().strftime("%Y-%m-%d"),
    )

    print(resultado)