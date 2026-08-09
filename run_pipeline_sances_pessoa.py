from config.logging import setup_logging
from pipelines.pessoa_pipeline import executar_pipeline_pessoa

setup_logging()


def executar_sances_pessoa():

    resultado = executar_pipeline_pessoa(tenant_id=1)
    return [{"resultado": resultado}]


if __name__ == "__main__":
    print(executar_sances_pessoa())