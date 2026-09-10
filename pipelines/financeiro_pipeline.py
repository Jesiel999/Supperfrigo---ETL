import logging

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.sances.financeiro import extrair_financeiro_sances
from silver.transform.sances.financeiro import transformar_financeiro, transformar_recebimentos
from config.settings import SANCES_TOKEN, URL_SANCES_FINANCEIRO, REQUEST_TIMEOUT, RATE_LIMIT_SLEEP, SLEEP_REQUEST
from repositories.offset_repository import ler_offset
from repositories.sances.financeiro_repository import upsert_financeiro_raw, buscar_raw_para_transform, upsert_financeiro_bi, buscar_recebimentos_raw_para_transform, upsert_recebimentos_bi
from repositories.tenant_repository import buscar_token_por_nome

logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────

class StepExtrairFinanceiro(Step):
    """Bronze: extrai da API Sances e grava em financeiro_raw com tenant_id."""

    def __init__(
        self,
        tenant_id:          int,
        token:              str,
        origem: str,
        limit: int = 100,
        offset_inicial: int | None = None,
        filtros: dict | None = None,
    ):
        super().__init__("ExtrairFinanceiro")
        self.tenant_id          = tenant_id
        self.token       = token
        self.origem = origem
        self.limit = limit
        self.offset_inicial = offset_inicial
        self.filtros = filtros

    def execute(self, context: dict) -> dict:
        resultado = extrair_financeiro_sances(
            tenant_id=self.tenant_id,
            origem=self.origem,
            token=self.token,
            limit=self.limit,
            offset_inicial=self.offset_inicial,
            filtros=self.filtros,
        )

        context["bronze_financeiro_resultado"] = resultado

        context["tenant_id"] = self.tenant_id

        return context


class StepTransformarFinanceiro(Step):
    """Silver: lê raw do tenant, transforma, grava em financeiro_bi e recebimentos_bi."""

    def __init__(self):
        super().__init__("TransformarFinanceiro")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]

        # Títulos
        registros_raw = buscar_raw_para_transform()
        registros_bi = transformar_financeiro(registros_raw, tenant_id=tenant_id)
        resultado = upsert_financeiro_bi(registros_bi)
        context["silver_financeiro_resultado"] = resultado

        # Recebimentos
        recebimentos_raw = buscar_recebimentos_raw_para_transform()
        recebimentos_bi = transformar_recebimentos(recebimentos_raw, tenant_id=tenant_id)
        resultado_recebimentos = upsert_recebimentos_bi(recebimentos_bi)
        context["silver_recebimentos_resultado"] = resultado_recebimentos

        return context

# ── Interface pública ─────────────────────────────────────────

def executar_pipeline_financeiro(
    tenant_id: int,
    origem: str,
    data_vencimento_inicial: str | None = None,
    data_vencimento_final: str | None = None,
    data_insercao_inicial: str | None = None,
    data_insercao_final: str | None = None,
    codigo_situacao: str | None = None,
    limit: int = 100,
    offset_inicial: int | None = None,
) -> dict:
    """
    origem: obrigatório — identifica a trilha de offset no banco.
            Ex: "financeiro_diario_baixa", "financeiro_total_a".
    """
    token = buscar_token_por_nome("SANCES_TOKEN")
    if not token:
        raise ValueError("Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config.")

    filtros: dict = {}
    if data_vencimento_inicial:
        filtros["data_vencimento_inicial"] = data_vencimento_inicial
    if data_vencimento_final:
        filtros["data_vencimento_final"] = data_vencimento_final
    if data_insercao_inicial:
        filtros["data_insercao_inicial"] = data_insercao_inicial
    if data_insercao_final:
        filtros["data_insercao_final"] = data_insercao_final
    if codigo_situacao:
        filtros["codigo_situacao"] = codigo_situacao

    # ---------------------------------------------------------
    # DESCOBRE OFFSET ATUAL
    # ---------------------------------------------------------
    offset = ler_offset(
        tenant_id=tenant_id,
        origem=origem,
        offset_inicial=offset_inicial,
    )

    conn = connection_mysql()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, offset_atual
            FROM pipeline_offset
            WHERE tenant_id = %s AND origem = %s
            LIMIT 1
            """,
            (tenant_id, origem),
        )
        pipeline_offset = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not pipeline_offset:
        raise RuntimeError(
            f"Registro pipeline_offset não encontrado para tenant={tenant_id}, origem={origem}."
        )

    pipeline = (
        Pipeline(f"FinanceiroPipeline-tenant{tenant_id}-{origem}")
        .add_step(StepExtrairFinanceiro(
            tenant_id=tenant_id,
            token=token,
            origem=origem,
            limit=limit,
            offset_inicial=offset,
            filtros=filtros,
        ))
        .add_step(StepTransformarFinanceiro())
    )

    return pipeline.run({
        "tenant_id": tenant_id,
        "pipeline_offset_id": pipeline_offset["id"],
        "offset_inicial": offset,
        "origem": origem,
        "endpoint": URL_SANCES_FINANCEIRO,
    })