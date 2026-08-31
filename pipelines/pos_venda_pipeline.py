import logging
from core.pipeline import Pipeline
from core.step import Step

from bronze.extract.sances.pos_venda import extrair_pos_venda_sances, ORIGEM as ORIGEM_POS_VENDA
from silver.transform.sances.pos_venda import processar_pos_venda_pendentes
from repositories.offset_repository import marcar_inicio_execucao, marcar_concluido, marcar_erro
from repositories.tenant_repository import buscar_token_por_nome
from config.settings import URL_SANCES_POS_VENDA

logger = logging.getLogger(__name__)


class StepExtrairPosVenda(Step):

    def __init__(
        self,
        tenant_id: int,
        token: str,
        limit: int = 100,
        offset_inicial: int | None = None,
        filtros: dict | None = None,
    ):
        super().__init__("ExtrairPosVenda")
        self.tenant_id = tenant_id
        self.token = token
        self.limit = limit
        self.offset_inicial = offset_inicial
        self.filtros = filtros

    def execute(self, context: dict) -> dict:
        marcar_inicio_execucao(
            tenant_id=self.tenant_id,
            origem=ORIGEM_POS_VENDA,
            endpoint=URL_SANCES_POS_VENDA,
        )

        try:
            resultado = extrair_pos_venda_sances(
                tenant_id=self.tenant_id,
                token=self.token,
                limit=self.limit,
                offset_inicial=self.offset_inicial,
                filtros=self.filtros,
            )
        except Exception as e:
            marcar_erro(self.tenant_id, ORIGEM_POS_VENDA, str(e))
            raise

        if resultado["status"] == "ERRO":
            marcar_erro(self.tenant_id, ORIGEM_POS_VENDA, "Falha na extração — ver logs da execução.")
        elif resultado["status"] == "CONCLUIDO":
            marcar_concluido(self.tenant_id, ORIGEM_POS_VENDA)

        context["bronze_pos_venda_resultado"] = resultado
        context["tenant_id"] = self.tenant_id
        logger.info(
            f"POS_VENDA | tenant={self.tenant_id} | páginas={resultado['paginas']} | "
            f"registros={resultado['registros']} | status={resultado['status']}"
        )
        return context


class StepTransformarPosVenda(Step):

    def __init__(self, limite_por_execucao: int = 500):
        super().__init__("TransformarPosVenda")
        self.limite_por_execucao = limite_por_execucao

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        resultado = processar_pos_venda_pendentes(tenant_id=tenant_id, limite=self.limite_por_execucao)
        context["silver_pos_venda_resultado"] = resultado
        logger.info(f"[SILVER-POS_VENDA] tenant={tenant_id} {resultado}")
        return context


def executar_pipeline_pos_venda(
    tenant_id: int,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
    limite_silver_por_execucao: int = 500,
) -> dict:
    token = buscar_token_por_nome("SANCES_TOKEN")
    if not token:
        raise ValueError("Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config.")

    pipeline = (
        Pipeline(f"PosVendaPipeline-tenant{tenant_id}")
        .add_step(StepExtrairPosVenda(
            tenant_id=tenant_id,
            token=token,
            limit=limit,
            offset_inicial=offset_inicial,
            filtros=filtros,
        ))
        .add_step(StepTransformarPosVenda(limite_por_execucao=limite_silver_por_execucao))
    )

    return pipeline.run({"tenant_id": tenant_id})