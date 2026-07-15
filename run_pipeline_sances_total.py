from config.logging import setup_logging
from pipelines.financeiro_pipeline import executar_pipeline_financeiro

setup_logging()

# a (Em aberto), t (Baixado), p (Baixado parcial), c (Cancelado),
# r (Renegociado), u (Unido), x (Trânsito)
SITUACOES = ["a", "t", "p", "c", "r", "u", "x"]

def executar_sances_total():
    """
    Roda o pipeline completo para cada codigo_situacao.
    Cada situação tem seu próprio arquivo de offset, então a paginação
    de uma não interfere na outra, e cada uma "varia" (avança/reseta)
    de forma independente quando a página vem em branco.
    """
    resultados = []
    for situacao in SITUACOES:
        resultado = executar_pipeline_financeiro(
            tenant_id=1,
            codigo_situacao=situacao,
            offset_file=f"logs/bronze/financeiro_offset_total_{situacao}.txt",
        )
        resultados.append({"codigo_situacao": situacao, "resultado": resultado})

    return resultados

if __name__ == "__main__":
    print(executar_sances_total())