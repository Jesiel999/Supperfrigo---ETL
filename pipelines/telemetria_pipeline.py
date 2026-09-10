import logging

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.econnect.telemetria import extrair_telemetria_econnect, ORIGEM as ORIGEM_TELEMETRIA_ECONNECT
from silver.transform.veiculos.telemetria import processar_telemetria_pendentes
from repositories.econnect.telemetria_repository import upsert_telemetria_raw
from repositories.offset_repository import marcar_inicio_execucao, marcar_concluido, marcar_erro, ler_offset
from repositories.tenant_repository import buscar_token_por_nome
from config.settings import URL_ECONNECT_TELEMETRIA

logger = logging.getLogger(__name__)


class StepExtrairTelemetria(Step):

    def __init__(self, 
        tenant_id: int,
        offset_inicial: int | None = None,
        ):

        super().__init__("ExtrairTelemetria")

        self.tenant_id = tenant_id
        self.offset_inicial = offset_inicial

    def execute(self, context: dict) -> dict:

        resultado = extrair_telemetria_econnect(
            tenant_id=self.tenant_id,
            endpoint=URL_ECONNECT_TELEMETRIA,
            offset_inicial=self.offset_inicial,
        )

        context["bronze_telemetria_resultado"] = resultado
        
        context["tenant_id"] = self.tenant_id

        # logger.info(
        #    f"[BRONZE-ESTOQUE] "
        #    f"tenant={self.tenant_id} | "
        #    f"páginas={resultado.get('paginas', 0)} | "
        #    f"registros={resultado.get('registros', 0)} | "
        #    f"status={resultado.get('status')}"
        # )

        return context

class StepTransformarTelemetria(Step):

    def __init__(
        self,
        limite_por_execucao: int = 1000
    ):

        super().__init__("TransformarTelemetria")

        self.limite_por_execucao = limite_por_execucao

    def execute(
        self, 
        context: dict
    ) -> dict:

        tenant_id = context["tenant_id"]

        resultado = processar_telemetria_pendentes(
            tenant_id=tenant_id, 
            pipeline=ORIGEM_TELEMETRIA_ECONNECT,
            limite=self.limite_por_execucao
        )

        context["silver_telemetria_resultado"] = resultado

        # logger.info(
        #    f"[SILVER-TELEMETRIA] "
        #    f"tenant={tenant_id} | " 
        #    f"{resultado}"
        #)

        return context


def executar_pipeline_telemetria(
    tenant_id: int,
    offset_inicial: int | None = None,
    limite_silver_por_execucao: int = 1000
) -> dict:

    # ---------------------------------------------------------
    # DESCOBRE OFFSET ATUAL
    # ---------------------------------------------------------

    offset = ler_offset(
        tenant_id=tenant_id,
        origem=ORIGEM_TELEMETRIA_ECONNECT,
        offset_inicial=offset_inicial,
    )

    # ---------------------------------------------------------
    # O pipeline_offset_id é necessário para relacionar
    # a execução ao registro de controle.
    # ---------------------------------------------------------

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
                ORIGEM_TELEMETRIA_ECONNECT,
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
            f"origem={ORIGEM_TELEMETRIA_ECONNECT}."
        )

    pipeline = (
        Pipeline(
            f"EstoquePipeline-tenant{tenant_id}"
        )

        .add_step(
            StepExtrairTelemetria(
                tenant_id=tenant_id,
                offset_inicial=offset,
            )
        )

        .add_step(
            StepTransformarTelemetria(
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
                ORIGEM_TELEMETRIA_ECONNECT,

            "endpoint":
                URL_ECONNECT_TELEMETRIA,
        }
    )