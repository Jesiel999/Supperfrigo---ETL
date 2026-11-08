from config.logging import setup_logging
from pipelines.estoque_veiculos_pipeline import executar_pipeline_estoque_veiculos

setup_logging()

TENANT_ID = 1


def executar_sances_estoque_veiculos():
    resultado = executar_pipeline_estoque_veiculos(tenant_id=TENANT_ID, modo="incremental")
    return [{"resultado": resultado}]


def executar_sances_estoque_veiculos_completo():
    # varredura sem filtro de data + incluir_indisponiveis: detecta as saídas
    resultado = executar_pipeline_estoque_veiculos(
        tenant_id=TENANT_ID, modo="completo", incluir_custos=True
    )
    return [{"resultado": resultado}]


if __name__ == "__main__":
    print(executar_sances_estoque_veiculos())