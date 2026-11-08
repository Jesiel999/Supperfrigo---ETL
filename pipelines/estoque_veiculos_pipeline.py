import logging
from datetime import datetime, timedelta

from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql
from bronze.extract.sances.estoque_veiculos import extrair_estoque_veiculos_sances
from silver.transform.sances.estoque_veiculos import transformar_estoque_veiculos
from config.settings import URL_SANCES_ESTOQUE_VEICULOS
from repositories.offset_repository import ler_offset
from repositories.sances.estoque_veiculos_repository import (
    buscar_raw_para_transform,
    upsert_veiculo_estoque_bi,
)
from repositories.tenant_repository import buscar_token_por_nome

logger = logging.getLogger(__name__)

MODOS = ("incremental", "completo")

# ── Steps ─────────────────────────────────────────────────────

class StepExtrairEstoqueVeiculos(Step):
    """Bronze: extrai da API Sances (v2) e grava em veiculo_estoque_raw com tenant_id."""

    def __init__(
        self,
        tenant_id: int,
        token: str,
        origem: str,
        limit: int = 500,
        offset_inicial: int | None = None,
        filtros: dict | None = None,
    ):
        super().__init__("ExtrairEstoqueVeiculos")
        self.tenant_id = tenant_id
        self.token = token
        self.origem = origem
        self.limit = limit
        self.offset_inicial = offset_inicial
        self.filtros = filtros

    def execute(self, context: dict) -> dict:
        resultado = extrair_estoque_veiculos_sances(
            tenant_id=self.tenant_id,
            origem=self.origem,
            token=self.token,
            limit=self.limit,
            offset_inicial=self.offset_inicial,
            filtros=self.filtros,
        )

        context["bronze_estoque_resultado"] = resultado

        # WARNING de propósito, para aparecer mesmo com o logger em nível alto.
        logger.warning(
            f"[estoque_veiculos] extração origem={self.origem} "
            f"filtros={self.filtros} -> {resultado}"
        )
        context["tenant_id"] = self.tenant_id

        return context


class StepTransformarEstoqueVeiculos(Step):
    def __init__(self):
        super().__init__("TransformarEstoqueVeiculos")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]

        registros_raw = buscar_raw_para_transform(tenant_id)
        registros_bi = transformar_estoque_veiculos(registros_raw, tenant_id=tenant_id)

        context["silver_estoque_resultado"] = upsert_veiculo_estoque_bi(registros_bi)

        return context


# ── Interface pública ─────────────────────────────────────────

def executar_pipeline_estoque_veiculos(
    tenant_id: int,
    modo: str = "incremental",
    origem: str | None = None,
    alterado_desde: str | None = None,
    alterado_ate: str | None = None,
    cnpj_empresa: str | None = None,
    incluir_custos: bool = False,
    limit: int = 500,
    offset_inicial: int | None = None,
) -> dict:
    """
    modo="incremental": filtra por alterado_desde (default: últimos 2 dias).
        Pega cadastro e mudança de PREÇO, mas NÃO venda/reserva/bloqueio.
    modo="completo": varredura sem filtro de data + incluir_indisponiveis=true.
        Rodar ao menos 1x/dia: é ela que detecta as saídas (ativo_no_estoque=false).
    """
    if modo not in MODOS:
        raise ValueError(f"modo inválido: {modo!r} (use {MODOS})")

    origem = origem or f"sances_estoque_veiculos_{modo}"

    token = buscar_token_por_nome("SANCES_TOKEN")
    if not token:
        raise ValueError("Token SANCES_TOKEN não encontrado (ou inativo) em tenant_config.")

    filtros: dict = {}

    if modo == "completo":
        filtros["incluir_indisponiveis"] = "true"
    else:
        filtros["alterado_desde"] = alterado_desde or (
            datetime.now() - timedelta(days=2)
        ).strftime("%Y-%m-%dT%H:%M:%S")

        if alterado_ate:
            filtros["alterado_ate"] = alterado_ate

    if cnpj_empresa:
        filtros["cnpj_empresa"] = cnpj_empresa
    if incluir_custos:
        filtros["incluir_custos"] = "true"

    offset = ler_offset(
        tenant_id=tenant_id,
        origem=origem,
        offset_inicial=offset_inicial,
    )

    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
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
        Pipeline(f"EstoqueVeiculosPipeline-tenant{tenant_id}-{origem}")
        .add_step(StepExtrairEstoqueVeiculos(
            tenant_id=tenant_id,
            token=token,
            origem=origem,
            limit=limit,
            offset_inicial=offset,
            filtros=filtros,
        ))
        .add_step(StepTransformarEstoqueVeiculos())
    )

    return pipeline.run({
        "tenant_id": tenant_id,
        "pipeline_offset_id": pipeline_offset["id"],
        "offset_inicial": offset,
        "origem": origem,
        "modo": modo,
        "endpoint": URL_SANCES_ESTOQUE_VEICULOS,
    })