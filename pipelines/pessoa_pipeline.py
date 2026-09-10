import logging

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.sances.pessoa import extrair_pessoa_sances, ORIGEM as ORIGEM_PESSOA_SANCES
from bronze.extract.sults.pessoa import extrair_pessoa_sults, ORIGEM as ORIGEM_PESSOA_SULTS
from silver.transform.pessoa.pessoa import transformar_pessoa
from repositories.pessoa_repository import buscar_raw_para_transform, upsert_pessoa_bi
from repositories.offset_repository import ler_offset
from repositories.tenant_repository import buscar_token_por_nome

logger = logging.getLogger(__name__)


class StepExtrairPessoaSances(Step):

    def __init__(
        self,
        tenant_id: int,
        token: str,
        offset_inicial: int | None = None,
        quantidade_por_execucao: int = 5000,
    ):

        super().__init__("ExtrairPessoaSances")

        self.tenant_id = tenant_id
        self.token = token
        self.offset_inicial = offset_inicial
        self.quantidade_por_execucao = quantidade_por_execucao

    def execute(self, context: dict) -> dict:

        resultado = extrair_pessoa_sances(
            tenant_id=self.tenant_id,
            token=self.token,
            offset_inicial=self.offset_inicial,
            quantidade_por_execucao=self.quantidade_por_execucao,
        )

        context["bronze_sances_resultado"] = resultado

        context["tenant_id"] = self.tenant_id

        return context


class StepExtrairPessoaSults(Step):

    def __init__(
        self,
        tenant_id: int,
        token: str, 
        offset_inicial: int | None = None
    ):

        super().__init__("ExtrairPessoaSults")

        self.tenant_id = tenant_id
        self.token = token
        self.offset_inicial = offset_inicial

    def execute(self, context: dict) -> dict:

        resultado = extrair_pessoa_sults(
            tenant_id=self.tenant_id,
            token=self.token,
            limit=100,
            offset_inicial=self.offset_inicial,
        )

        context["bronze_sults_resultado"] = resultado
        
        context["tenant_id"] = self.tenant_id
        
        return context


class StepTransformarPessoa(Step):

    def __init__(self):

        super().__init__("TransformarPessoa")

    def execute(
        self, 
        context: dict
    ) -> dict:
        tenant_id = context["tenant_id"]
        raw = buscar_raw_para_transform()
        registros_bi = transformar_pessoa(raw, tenant_id=tenant_id)
        resultado = upsert_pessoa_bi(registros_bi)
        context["silver_resultado"] = resultado
        context["silver_total"] = len(registros_bi)
        return context


def _garantir_pipeline_offset(tenant_id: int, origem: str) -> dict:
    conn = connection_mysql()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, offset_atual FROM pipeline_offset WHERE tenant_id = %s AND origem = %s LIMIT 1",
            (tenant_id, origem),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        raise RuntimeError(
            f"Registro pipeline_offset não encontrado para tenant={tenant_id}, origem={origem}."
        )
    return row


def executar_pipeline_pessoa(
    tenant_id: int,
    offset_inicial_sances: int | None = None,
    offset_inicial_sults: int | None = None,
    quantidade_por_execucao_sances: int = 5000,
) -> dict:

    token_sances = buscar_token_por_nome(
        "SANCES_TOKEN"
    )
    token_sults = buscar_token_por_nome(
        "SULTS_TOKEN"
    )

    if not token_sances:
        raise ValueError("Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config.")
    if not token_sults:
        raise ValueError("Token SULTS_TOKEN não encontrado (ou inativo) em tenant_config.")

    # ---------------------------------------------------------
    # DESCOBRE OFFSET ATUAL (mesmo padrão do estoque)
    # ---------------------------------------------------------
    _garantir_pipeline_offset(tenant_id, ORIGEM_PESSOA_SANCES)
    _garantir_pipeline_offset(tenant_id, ORIGEM_PESSOA_SULTS)

    offset_sances = ler_offset(tenant_id=tenant_id, origem=ORIGEM_PESSOA_SANCES, offset_inicial=offset_inicial_sances)
    offset_sults = ler_offset(tenant_id=tenant_id, origem=ORIGEM_PESSOA_SULTS, offset_inicial=offset_inicial_sults)

    pipeline = (
        Pipeline(f"PessoaPipeline-tenant{tenant_id}")
        .add_step(StepExtrairPessoaSances(
            tenant_id=tenant_id,
            token=token_sances,
            offset_inicial=offset_sances,
            quantidade_por_execucao=quantidade_por_execucao_sances,
        ))
        .add_step(StepExtrairPessoaSults(
            tenant_id=tenant_id,
            token=token_sults,
            offset_inicial=offset_sults,
        ))
        .add_step(StepTransformarPessoa())
    )

    return pipeline.run({"tenant_id": tenant_id})


def executar_todos_tenants() -> list[dict]:
    from repositories.tenant_repository import listar_tenants_ativos

    tenants = listar_tenants_ativos()
    resultados = []

    for t in tenants:
        try:
            res = executar_pipeline_pessoa(tenant_id=t["id"])
            resultados.append({"tenant_id": t["id"], "status": "ok", **res})
        except Exception as e:
            logger.error(f"Erro no tenant {t['id']}: {e}")
            resultados.append({"tenant_id": t["id"], "status": "erro", "erro": str(e)})

    return resultados