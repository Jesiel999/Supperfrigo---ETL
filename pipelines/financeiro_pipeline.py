import logging
from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql

from bronze.extract.sances.financeiro import extrair_financeiro
from silver.transform.sances.financeiro.financeiro import transformar_financeiro
from gold.marts.sances.inadimplencia import processar_inadimplencia
from gold.marts.sances.pmp import processar_pmp
from gold.marts.sances.pmr import processar_pmr

from repositories.financeiro_repository import (
    upsert_financeiro_raw,
    buscar_raw_para_transform,
    upsert_financeiro_bi,
    upsert_pmp_gold,
    upsert_pmr_gold
)
from repositories.tenant_repository import buscar_config_tenant

logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────

class StepExtrairFinanceiro(Step):
    """Bronze: extrai da API Sances e grava em financeiro_raw com tenant_id."""

    def __init__(
        self,
        tenant_id:          int,
        token:              str,
        data_baixa_inicial: str | None = None,
        data_baixa_final:   str | None = None,
        data_vencimento_inicial: str | None = None,
        data_vencimento_final: str | None = None,
    ):
        super().__init__("ExtrairFinanceiro")
        self.tenant_id          = tenant_id
        self.token       = token
        self.data_baixa_inicial = data_baixa_inicial
        self.data_baixa_final   = data_baixa_final
        self.data_vencimento_inicial = data_vencimento_inicial
        self.data_vencimento_final = data_vencimento_final

    def execute(self, context: dict) -> dict:
        registros = extrair_financeiro(
            limit=100,
            data_baixa_inicial=self.data_baixa_inicial,
            data_baixa_final=self.data_baixa_final,
            data_vencimento_inicial=self.data_vencimento_inicial,
            data_vencimento_final=self.data_vencimento_final,
        )

        # Injeta tenant_id em cada registro antes de gravar
        for r in registros:
            r["tenant_id"] = self.tenant_id

        resultado = upsert_financeiro_raw(registros)
        context["bronze_resultado"] = resultado
        context["bronze_total"]     = len(registros)
        context["tenant_id"]        = self.tenant_id
        logger.info(f"[BRONZE] tenant={self.tenant_id} {resultado}")
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


class StepProcessarInadimplencia(Step):
    """Gold: processa inadimplência para o tenant."""

    def __init__(self):
        super().__init__("ProcessarInadimplencia")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        resultado = processar_inadimplencia()
        context["gold_resultado"] = resultado
        logger.info(f"[GOLD] tenant={tenant_id} {resultado}")
        return context

class StepProcessarPmp(Step):
    """Gold: processa Prazo medio de pagamento para o tenant."""

    def __init__(self):
        super().__init__("ProcessarPmp")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        resultado = processar_pmp()
        context["gold_resultado"] = resultado
        logger.info(f"[GOLD] tenant={tenant_id} {resultado}")
        return context


class StepProcessarPmr(Step):
    """Gold: processa Prazo medio de recebimento para o tenant."""

    def __init__(self):
        super().__init__("ProcessarPmr")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        resultado = processar_pmr()
        context["gold_resultado"] = resultado
        logger.info(f"[GOLD] tenant={tenant_id} {resultado}")
        return context


# ── Interface pública ─────────────────────────────────────────

def executar_pipeline_financeiro(
    tenant_id:          int,
    data_baixa_inicial: str | None = None,
    data_baixa_final:   str | None = None,
    data_vencimento_inicial: str | None = None,
    data_vencimento_final: str | None = None,
) -> dict:
    """
    Executa o pipeline completo Bronze → Silver → Gold
    para um tenant específico.

    O token da API Sances é buscado na tabela tenant_config.
    
    """

    def buscar_config_tenant(tenant_id: int):
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

    config = buscar_config_tenant(1)
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
            data_baixa_inicial=data_baixa_inicial,
            data_baixa_final=data_baixa_final,
            data_vencimento_inicial=data_vencimento_inicial,
            data_vencimento_final=data_vencimento_final,
        ))
        .add_step(StepTransformarFinanceiro())
        .add_step(StepProcessarInadimplencia())
        .add_step(StepProcessarPmp())
        .add_step(StepProcessarPmr())
    )

    return pipeline.run({"tenant_id": tenant_id})


def executar_todos_tenants(
    data_baixa_inicial: str | None = None,
    data_baixa_final:   str | None = None,
    data_vencimento_inicial: str | None = None,
    data_vencimento_final: str | None = None,
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
                data_baixa_inicial=data_baixa_inicial,
                data_baixa_final=data_baixa_final,
                data_vencimento_inicial=data_vencimento_inicial,
                data_vencimento_final=data_vencimento_final,
            )
            resultados.append({"tenant_id": t["id"], "status": "ok", **res})
        except Exception as e:
            logger.error(f"Erro no tenant {t['id']}: {e}")
            resultados.append({"tenant_id": t["id"], "status": "erro", "erro": str(e)})

    return resultados
