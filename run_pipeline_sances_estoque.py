from config.logging import setup_logging
from pipelines.estoque_pipeline import executar_pipeline_estoque

setup_logging()


def executar_sances_estoque():

    resultado = executar_pipeline_estoque(tenant_id=1)
    return [{"resultado": resultado}]


if __name__ == "__main__":
    print(executar_sances_estoque())
