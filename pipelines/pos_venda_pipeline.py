import logging

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.sances.pos_venda import extrair_pos_venda_sances, ORIGEM as ORIGEM_POS_VENDA
from silver.transform.sances.pos_venda import processar_pos_venda_pendentes
from repositories.offset_repository import ler_offset
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

        resultado = extrair_pos_venda_sances(
            tenant_id=self.tenant_id,
            token=self.token,
            limit=self.limit,
            offset_inicial=self.offset_inicial,
            filtros=self.filtros,
        )

        context["bronze_pos_venda_resultado"] = resultado

        context["tenant_id"] = self.tenant_id

        return context

class StepTransformarPosVenda(Step):

    def __init__(self, limite_por_execucao: int | None = None):
        super().__init__("TransformarPosVenda")
        self.limite_por_execucao = limite_por_execucao

    def execute(self, context: dict) -> dict:

        tenant_id = context["tenant_id"]

        resultado = processar_pos_venda_pendentes(
            tenant_id=tenant_id,
            limite=self.limite_por_execucao,
        )

        context["silver_pos_venda_resultado"] = resultado

        return context
    
def executar_pipeline_pos_venda(
    tenant_id: int,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
    limite_silver_por_execucao: int | None = None,
) -> dict:

    token = buscar_token_por_nome(
        "SANCES_TOKEN"
    )

    if not token:
        raise ValueError(
            "Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config."
        )

    # ---------------------------------------------------------
    # DESCOBRE OFFSET ATUAL
    # ---------------------------------------------------------

    offset = ler_offset(
        tenant_id=tenant_id,
        origem=ORIGEM_POS_VENDA,
        offset_inicial=offset_inicial,
    )

    conn = connection_mysql()

    try:

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                offset_atual
            FROM pipeline_offset
            WHERE tenant_id = %s
              AND origem = %s
            LIMIT 1
            """,
            (
                tenant_id,
                ORIGEM_POS_VENDA,
            ),
        )

        pipeline_offset = cursor.fetchone()

    finally:

        cursor.close()
        conn.close()

    # ---------------------------------------------------------
    # SE NÃO EXISTIR PIPELINE_OFFSET
    # ---------------------------------------------------------
    
    if not pipeline_offset:

        raise RuntimeError(
            "Registro pipeline_offset não encontrado "
            f"para tenant={tenant_id}, "
            f"origem={ORIGEM_POS_VENDA}."
        )

    pipeline = (
        Pipeline(
            f"PosVendaPipeline-tenant{tenant_id}"
        )

        .add_step(
            StepExtrairPosVenda(
                tenant_id=tenant_id,
                token=token,
                limit=limit,
                offset_inicial=offset,
                filtros=filtros,
            )
        )

        .add_step(
            StepTransformarPosVenda(
                limite_por_execucao=
                    limite_silver_por_execucao
            )
        )
    )

    return pipeline.run(
        {
            "tenant_id": tenant_id,

            "pipeline_offset_id":
                pipeline_offset["id"],

            "offset_inicial":
                offset,

            "origem":
                ORIGEM_POS_VENDA,

            "endpoint":
                URL_SANCES_POS_VENDA,
        }
    )
