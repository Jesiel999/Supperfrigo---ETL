from config.logging import setup_logging
from pipelines.pos_venda_pipeline import executar_pipeline_pos_venda

setup_logging()

def executar_sances_pos_venda():
    return executar_pipeline_pos_venda(tenant_id=1)

if __name__ == "__main__":
    print(executar_sances_pos_venda())