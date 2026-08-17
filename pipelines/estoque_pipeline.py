import logging
from core.pipeline import Pipeline
from core.step import Step

from bronze.extract.sances.estoque import extrair_estoque_sances, ORIGEM as ORIGEM_ESTOQUE_SANCES
from silver.transform.sances.estoque import processar_produtos_pendentes
from repositories.offset_repository import marcar_inicio_execucao, marcar_concluido, marcar_erro
from repositories.tenant_repository import buscar_token_por_nome
from config.settings import URL_SANCES_ESTOQUE

logger = logging.getLogger(__name__)

# ── Steps ─────────────────────────────────────────────────────

class StepExtrairEstoque(Step):

    def __init__(
        self,
        tenant_id: int,
        token: str,
        limit: int = 100,
        offset_inicial: int | None = None,
        filtros: dict | None = None,
    ):
        super().__init__("ExtrairEstoque")
        self.tenant_id = tenant_id
        self.token = token
        self.limit = limit
        self.offset_inicial = offset_inicial
        self.filtros = filtros

    def execute(self, context: dict) -> dict:
        marcar_inicio_execucao(
            tenant_id=self.tenant_id,
            origem=ORIGEM_ESTOQUE_SANCES,
            endpoint=URL_SANCES_ESTOQUE,
        )

        try:
            resultado = extrair_estoque_sances(
                tenant_id=self.tenant_id,
                token=self.token,
                limit=self.limit,
                offset_inicial=self.offset_inicial,
                filtros=self.filtros,
            )
        except Exception as e:
            marcar_erro(self.tenant_id, ORIGEM_ESTOQUE_SANCES, str(e))
            raise

        if resultado["status"] == "ERRO":
            marcar_erro(self.tenant_id, ORIGEM_ESTOQUE_SANCES, "Falha na extração — ver logs da execução.")
        elif resultado["status"] == "CONCLUIDO":
            marcar_concluido(self.tenant_id, ORIGEM_ESTOQUE_SANCES)

        context["bronze_estoque_resultado"] = resultado
        context["tenant_id"] = self.tenant_id
        logger.info(
            f"ESTOQUE | tenant={self.tenant_id} | páginas={resultado['paginas']} | "
            f"registros={resultado['registros']} | status={resultado['status']}"
        )
        return context


class StepTransformarEstoque(Step):
    """Silver: lê produtos pendentes na Bronze e faz upsert nas 4 tabelas normalizadas."""

    def __init__(self, limite_por_execucao: int = 500):
        super().__init__("TransformarEstoque")
        self.limite_por_execucao = limite_por_execucao

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        resultado = processar_produtos_pendentes(
            tenant_id=tenant_id,
            pipeline=ORIGEM_ESTOQUE_SANCES,
            limite=self.limite_por_execucao,
        )
        context["silver_estoque_resultado"] = resultado
        logger.info(f"[SILVER-ESTOQUE] tenant={tenant_id} {resultado}")
        return context

def executar_pipeline_estoque(
    tenant_id: int,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
    limite_silver_por_execucao: int = 500,
) -> dict:
    """
    Executa Bronze (extração + persistência separada, sem JSON) → Silver
    (upsert normalizado com chaves compostas tenant_id+codigo_produto[+empresa/modelo]).

    Gold (estoque_gold) é uma VIEW — não precisa de step próprio, já reflete
    o dado mais recente da Silver automaticamente.
    """
    token = buscar_token_por_nome("SANCES_TOKEN")
    if not token:
        raise ValueError("Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config.")

    pipeline = (
        Pipeline(f"EstoquePipeline-tenant{tenant_id}")
        .add_step(StepExtrairEstoque(
            tenant_id=tenant_id,
            token=token,
            limit=limit,
            offset_inicial=offset_inicial,
            filtros=filtros,
        ))
        .add_step(StepTransformarEstoque(limite_por_execucao=limite_silver_por_execucao))
    )

    return pipeline.run({"tenant_id": tenant_id})
