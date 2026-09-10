# run_pipeline_sances_financeiro.py — DIÁRIO (07h–19h)
from datetime import datetime
import calendar
from config.logging import setup_logging
from pipelines.financeiro_pipeline import executar_pipeline_financeiro

setup_logging()

MODOS_DIARIO = ["baixa", "insercao"]

def executar_sances_diario():
    hoje = datetime.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])

    resultados = []
    for modo in MODOS_DIARIO:
        if modo == "baixa":
            kwargs = dict(
                data_vencimento_inicial=primeiro_dia.strftime("%Y-%m-%d"),
                data_vencimento_final=ultimo_dia.strftime("%Y-%m-%d"),
            )
        else:
            kwargs = dict(
                data_insercao_inicial=primeiro_dia.strftime("%Y-%m-%d"),
                data_insercao_final=ultimo_dia.strftime("%Y-%m-%d"),
            )

        resultado = executar_pipeline_financeiro(
            tenant_id=1,
            origem=f"financeiro_diario_{modo}",
            **kwargs,
        )
        resultados.append({"modo": modo, "resultado": resultado})

    return resultados

if __name__ == "__main__":
    print(executar_sances_diario())