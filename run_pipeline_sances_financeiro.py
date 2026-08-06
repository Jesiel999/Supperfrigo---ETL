from datetime import datetime
import calendar
from config.logging import setup_logging
from pipelines.financeiro_pipeline import executar_pipeline_financeiro

setup_logging()

# cada modo usa um filtro de data diferente e um offset próprio,
# assim uma passada não interfere na paginação da outra
MODOS_DIARIO = ["baixa", "insercao"]

def executar_sances_diario():
    hoje = datetime.now()

    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    
    resultados = []

    for modo in MODOS_DIARIO:
        if modo == "baixa":
            kwargs = dict(
                data_vencimento_inicial=primeiro_dia,
                data_vencimento_final=ultimo_dia,
            )
        else:  # insercao
            kwargs = dict(
                data_insercao_inicial=primeiro_dia,
                data_insercao_final=ultimo_dia,
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