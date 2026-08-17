import logging
from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql

from bronze.extract.sances.financeiro import extrair_financeiro
from silver.transform.sances.financeiro import transformar_financeiro

from repositories.sances.financeiro_repository import (
    upsert_financeiro_raw,
    buscar_raw_para_transform,
    upsert_financeiro_bi
)
from repositories.tenant_repository import buscar_token_por_nome

logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────

class StepExtrairFinanceiro(Step):
    """Bronze: extrai da API Sances e grava em financeiro_raw com tenant_id."""

    def __init__(
        self,
        tenant_id:          int,
        token:              str,
        data_vencimento_inicial: str | None = None,
        data_vencimento_final:   str | None = None,
        data_insercao_inicial: str | None = None,
        data_insercao_final: str | None = None,
        codigo_situacao: str | None = None,
        offset_file: str | None = None
    ):
        super().__init__("ExtrairFinanceiro")
        self.tenant_id          = tenant_id
        self.token       = token
        self.data_vencimento_inicial = data_vencimento_inicial
        self.data_vencimento_final   = data_vencimento_final
        self.data_insercao_inicial = data_insercao_inicial
        self.data_insercao_final = data_insercao_final
        self.codigo_situacao = codigo_situacao
        self.offset_file = offset_file or f"logs/bronze/financeiro_offset_{self.tenant_id}.txt"

    def execute(self, context: dict) -> dict:
        registros = extrair_financeiro(
            limit=100,
            data_vencimento_inicial=self.data_vencimento_inicial,
            data_vencimento_final=self.data_vencimento_final,
            data_insercao_inicial=self.data_insercao_inicial,
            data_insercao_final=self.data_insercao_final,
            codigo_situacao=self.codigo_situacao,
            offset_file=self.offset_file,
        )

        # Injeta tenant_id em cada registro antes de gravar
        for r in registros:
            r["tenant_id"] = self.tenant_id

        resultado = upsert_financeiro_raw(registros)
        context["bronze_resultado"] = resultado
        context["bronze_total"]     = len(registros)
        context["tenant_id"]        = self.tenant_id
        logger.info(f"[BRONZE] tenant={self.tenant_id} situacao={self.codigo_situacao} {resultado}")
        return context


class StepTransformarFinanceiro(Step):
    """Silver: lê raw do tenant, transforma, grava em financeiro_bi."""

    def __init__(self):
        super().__init__("TransformarFinanceiro")

    def execute(self, context: dict) -> dict:
        tenant_id     = context["tenant_id"]
        registros_raw = buscar_raw_para_transform()
        registros_bi  = transformar_financeiro(registros_raw, tenant_id=tenant_id)
        resultado     = upsert_financeiro_bi(registros_bi)
        context["silver_resultado"] = resultado
        context["silver_total"]     = len(registros_bi)
        logger.info(f"[SILVER] tenant={tenant_id} {resultado}")
        return context


# ── Interface pública ─────────────────────────────────────────

def executar_pipeline_financeiro(
    tenant_id:          int,
    data_vencimento_inicial: str | None = None,
    data_vencimento_final:   str | None = None,
    data_insercao_inicial: str | None = None,
    data_insercao_final: str | None = None,
    codigo_situacao: str | None = None,
    offset_file: str | None = None,
) -> dict:
    """
    Executa o pipeline completo Bronze → Silver → Gold
    para um tenant específico.

    O token da API Sances é buscado na tabela tenant_config.
    
    """

    def buscar_token_por_nome(tenant_id: int):
        conn = connection_mysql()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                tenant_id,
                token,
                token,
                ativo
            FROM tenant_config
            WHERE tenant_id = %s
            AND ativo = 1
        """, (tenant_id,))

        config = cursor.fetchone()

        cursor.close()
        conn.close()

        return config

    config = buscar_token_por_nome(1)
    if not config:
        raise ValueError(f"Tenant {tenant_id} não encontrado ou sem configuração.")

    token = config.get("token")
    if not token:
        raise ValueError(f"Tenant {tenant_id} sem token Sances configurado.")

    pipeline = (
        Pipeline(f"FinanceiroPipeline-tenant{tenant_id}")
        .add_step(StepExtrairFinanceiro(
            tenant_id=tenant_id,
            token=token,
            data_vencimento_inicial=data_vencimento_inicial,
            data_vencimento_final=data_vencimento_final,
            data_insercao_inicial=data_insercao_inicial,
            data_insercao_final=data_insercao_final,
            codigo_situacao=codigo_situacao,
            offset_file=offset_file,
        ))
        .add_step(StepTransformarFinanceiro())
    )

    return pipeline.run({"tenant_id": tenant_id})


def executar_todos_tenants(
    data_vencimento_inicial: str | None = None,
    data_vencimento_final:   str | None = None,
    data_insercao_inicial: str | None = None,
    data_insercao_final: str | None = None,
) -> list[dict]:
    """
    Executa o pipeline para TODOS os tenants ativos.
    Usado pelo agendador (cron/systemd).
    """
    from repositories.tenant_repository import listar_tenants_ativos

    tenants   = listar_tenants_ativos()
    resultados = []

    for t in tenants:
        logger.info(f"Iniciando pipeline para tenant: {t['nome']} (id={t['id']})")
        try:
            res = executar_pipeline_financeiro(
                tenant_id=t["id"],
                data_vencimento_inicial=data_vencimento_inicial,
                data_vencimento_final=data_vencimento_final,
                data_insercao_inicial=data_insercao_inicial,
                data_insercao_final=data_insercao_final,
            )
            resultados.append({"tenant_id": t["id"], "status": "ok", **res})
        except Exception as e:
            logger.error(f"Erro no tenant {t['id']}: {e}")
            resultados.append({"tenant_id": t["id"], "status": "erro", "erro": str(e)})

    return resultados
