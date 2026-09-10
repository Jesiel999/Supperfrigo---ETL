import logging

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.sults.chamados import extrair_chamados, ORIGEM as ORIGEM_CHAMADOS_SULTS
from silver.transform.sults.chamados import transformar_chamados
from config.settings import URL_CHAMADOS
from repositories.offset_repository import ler_offset
from repositories.tenant_repository import buscar_token_por_nome
from repositories.sults.chamados_repository import buscar_raw_para_transform, upsert_chamados_raw, upsert_chamados_bi
from repositories.sults.chamados_apoio_repository import upsert_chamados_apoio_bi
from repositories.sults.chamados_etiqueta_repository import upsert_chamados_etiqueta_bi, upsert_dim_etiqueta

logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────

class StepExtrairChamados(Step):

    def __init__(
        self,
        tenant_id: int,
        token: str,
        limit: int = 100,
        offset_inicial: int | None = None,
        filtros: dict | None = None,
    ):

        super().__init__("ExtrairChamados")

        self.tenant_id = tenant_id
        self.token = token
        self.limit = limit
        self.offset_inicial = offset_inicial
        self.filtros = filtros

    def execute(self, context: dict) -> dict:

        resultado = extrair_chamados(
            tenant_id=self.tenant_id,
            token=self.token,
            limit=self.limit,
            offset_inicial=self.offset_inicial,
            filtros=self.filtros,
        )

        context["bronze_chamados_resultado"] = resultado

        context["tenant_id"] = self.tenant_id

        return context

class StepTransformarChamados(Step):

    def __init__(
        self,
        limite_por_execucao: int = 500,
    ):

        super().__init__("TransformarChamados")

        self.limite_por_execucao = limite_por_execucao

    def execute(
        self,
        context: dict,
    ) -> dict:

        tenant_id = context["tenant_id"]

        chamados_raw = buscar_raw_para_transform(
            tenant_id=tenant_id,
            limite=self.limite_por_execucao,
        )

        if not chamados_raw:

            context["silver_chamados_resultado"] = {
                "chamados": 0,
                "apoios": 0,
                "etiquetas": 0,
            }

            return context

        apoios_raw = _buscar_apoios_raw(
            tenant_id
        )

        etiquetas_raw = _buscar_etiquetas_raw(
            tenant_id
        )

        transformacao = transformar_chamados(
            chamados_raw=chamados_raw,
            apoios_raw=apoios_raw,
            etiquetas_raw=etiquetas_raw,
            tenant_id=tenant_id,
        )

        res_chamados_bi = upsert_chamados_bi(
            transformacao["chamados"]
        )

        res_apoios_bi = upsert_chamados_apoio_bi(
            transformacao["apoios"]
        )

        res_etiquetas_bi = upsert_chamados_etiqueta_bi(
            transformacao["etiquetas"]
        )

        dim_etiquetas = _montar_dim_etiqueta(
            transformacao["etiquetas"]
        )

        res_dim_etiqueta = upsert_dim_etiqueta(
            dim_etiquetas
        )

        resultado = {
            "chamados": res_chamados_bi,
            "apoios": res_apoios_bi,
            "etiquetas": res_etiquetas_bi,
            "dim_etiqueta": res_dim_etiqueta,
        }

        context["silver_chamados_resultado"] = resultado

        return context


def executar_pipeline_chamados(
    tenant_id: int,
    limit: int = 100,
    offset_inicial: int | None = None,
    filtros: dict | None = None,
    limite_silver_por_execucao: int = 500,
) -> dict:

    token = buscar_token_por_nome(
        "SULTS_TOKEN"
    )

    if not token:
        raise ValueError(
            "Token SULTS_TOKEN não encontrado "
            "(ou inativo) em tenant_config."
        )

    # ---------------------------------------------------------
    # DESCOBRE OFFSET ATUAL
    # ---------------------------------------------------------

    offset = ler_offset(
        tenant_id=tenant_id,
        origem=ORIGEM_CHAMADOS_SULTS,
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
                ORIGEM_CHAMADOS_SULTS,
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
            f"origem={ORIGEM_CHAMADOS_SULTS}."
        )

    # ---------------------------------------------------------
    # MONTA PIPELINE
    # ---------------------------------------------------------

    pipeline = (
        Pipeline(
            f"ChamadosPipeline-tenant{tenant_id}"
        )

        .add_step(
            StepExtrairChamados(
                tenant_id=tenant_id,
                token=token,
                limit=limit,
                offset_inicial=offset,
                filtros=filtros,
            )
        )

        .add_step(
            StepTransformarChamados(
                limite_por_execucao=
                    limite_silver_por_execucao
            )
        )
    )

    # ---------------------------------------------------------
    # EXECUTA
    # ---------------------------------------------------------

    return pipeline.run(
        {
            "tenant_id": tenant_id,

            "pipeline_offset_id":
                pipeline_offset["id"],

            "offset_inicial":
                offset,

            "origem":
                ORIGEM_CHAMADOS_SULTS,

            "endpoint":
                URL_CHAMADOS,
        }
    )


def executar_todos_tenants(
    aberto: str | None = None,
) -> list[dict]:

    from repositories.tenant_repository import (
        listar_tenants_ativos
    )

    tenants = listar_tenants_ativos()

    resultados = []

    filtros = {}

    if aberto is not None:
        filtros["aberto"] = aberto

    for tenant in tenants:

        tenant_id = tenant["id"]

        try:

            resultado = executar_pipeline_chamados(
                tenant_id=tenant_id,
                limit=100,
                filtros=filtros or None,
                limite_silver_por_execucao=500,
            )

            resultados.append({
                "tenant_id": tenant_id,
                "status": "ok",
                **resultado,
            })

        except Exception as e:

            logger.exception(
                f"Erro no pipeline de chamados "
                f"tenant={tenant_id}"
            )

            resultados.append({
                "tenant_id": tenant_id,
                "status": "erro",
                "erro": str(e),
            })

    return resultados

    
# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def _buscar_apoios_raw(
    tenant_id: int,
) -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM chamados_apoio_raw
            WHERE tenant_id = %s
            """,
            (tenant_id,),
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def _buscar_etiquetas_raw(
    tenant_id: int,
) -> list[dict]:

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM chamados_etiqueta_raw
            WHERE tenant_id = %s
            """,
            (tenant_id,),
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def _montar_dim_etiqueta(etiquetas_bi: list[dict]) -> list[dict]:
    """
    Monta registros para tabela de dimensão (deduplicada).
    """
    
    etiquetas_unicas = {}
    
    for etiqueta in etiquetas_bi:
        etiqueta_id = etiqueta.get("etiqueta_id")
        
        if etiqueta_id not in etiquetas_unicas:
            etiquetas_unicas[etiqueta_id] = {
                "etiqueta_id": etiqueta_id,
            }
    
    return list(etiquetas_unicas.values())