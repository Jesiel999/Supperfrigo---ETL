from datetime import datetime
from config.logging import setup_logging
from pipelines.financeiro_pipeline import executar_pipeline_financeiro

setup_logging()

# cada modo usa um filtro de data diferente e um offset próprio,
# assim uma passada não interfere na paginação da outra
MODOS_DIARIO = ["baixa", "insercao"]

def executar_sances_diario():
    hoje = datetime.now().strftime("%Y-%m-%d")
    resultados = []

    for modo in MODOS_DIARIO:
        if modo == "baixa":
            kwargs = dict(
                data_baixa_inicial=hoje,
                data_baixa_final=hoje,
            )
        else:  # insercao
            kwargs = dict(
                data_insercao_inicial=hoje,
                data_insercao_final=hoje,
            )

        resultado = executar_pipeline_financeiro(
            tenant_id=1,
            offset_file=f"logs/bronze/financeiro_offset_diario_{modo}.txt",
            **kwargs,
        )
        resultados.append({"modo": modo, "resultado": resultado})

    return resultados

if __name__ == "__main__":
    print(executar_sances_diario())