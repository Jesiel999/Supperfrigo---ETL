import logging
from core.pipeline import Pipeline
from core.step import Step
from database.mysql_connection import connection_mysql

from bronze.extract.sults.chamados import extrair_chamados
from silver.transform.sults.chamados import transformar_chamados
from gold.marts.sults.chamados import processar_chamados_geral_gold

from repositories.sults.chamados_repository import (
    buscar_raw_para_transform,
    upsert_chamados_raw,
    upsert_chamados_bi,
)
from repositories.sults.chamados_apoio_repository import (
    upsert_chamados_apoio_bi,
)
from repositories.sults.chamados_etiqueta_repository import (
    upsert_chamados_etiqueta_bi,
    upsert_dim_etiqueta,
)

logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────

class StepExtrairChamados(Step):
    """Bronze: extrai da API e grava em chamados_raw com tenant_id."""

    def __init__(
        self,
        tenant_id: int,
        aberto: str | None = None,
    ):
        super().__init__("ExtrairChamados")
        self.tenant_id = tenant_id
        self.aberto = aberto

    def execute(self, context: dict) -> dict:
        registros = extrair_chamados(
            tenant_id=self.tenant_id,
            limit=100,
            aberto=self.aberto,
        )

        # Injeta tenant_id em cada registro
        if isinstance(registros, dict) and "chamados" in registros:
            # registros é um dict com chamados, apoios, etiquetas
            resultado = registros
        else:
            # Se retorna lista, converte
            resultado = {
                "chamados": registros if isinstance(registros, list) else [],
                "apoios": [],
                "etiquetas": [],
            }

        context["bronze_resultado"] = resultado
        context["bronze_total"] = len(resultado.get("chamados", []))
        context["tenant_id"] = self.tenant_id
        
        logger.info(f"[BRONZE] tenant={self.tenant_id}")
        return context


class StepTransformarChamados(Step):
    """Silver: lê raw do tenant, transforma, grava em chamados_bi."""

    def __init__(self):
        super().__init__("TransformarChamados")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        
        # Busca registros raw
        chamados_raw = buscar_raw_para_transform()
        
        if not chamados_raw:
            logger.warning(f"[SILVER] Nenhum registro raw encontrado para tenant={tenant_id}")
            context["silver_resultado"] = {
                "chamados": 0,
                "apoios": 0,
                "etiquetas": 0,
            }
            context["silver_total"] = 0
            return context
        
        # Busca apoios e etiquetas
        apoios_raw = _buscar_apoios_raw(tenant_id)
        etiquetas_raw = _buscar_etiquetas_raw(tenant_id)
        
        # Transforma
        transformacao = transformar_chamados(
            chamados_raw=chamados_raw,
            apoios_raw=apoios_raw,
            etiquetas_raw=etiquetas_raw,
            tenant_id=tenant_id,
        )
        
        # Upsert nas tabelas BI (exatamente como Financeiro)
        res_chamados_bi = upsert_chamados_bi(transformacao["chamados"])
        res_apoios_bi = upsert_chamados_apoio_bi(transformacao["apoios"])
        res_etiquetas_bi = upsert_chamados_etiqueta_bi(transformacao["etiquetas"])
        
        # Carrega dimensão
        dim_etiquetas = _montar_dim_etiqueta(transformacao["etiquetas"])
        res_dim_etiqueta = upsert_dim_etiqueta(dim_etiquetas)
        
        resultado = {
            "chamados": res_chamados_bi,
            "apoios": res_apoios_bi,
            "etiquetas": res_etiquetas_bi,
            "dim_etiqueta": res_dim_etiqueta,
        }
        
        context["silver_resultado"] = resultado
        context["silver_total"] = len(transformacao["chamados"])
        
        logger.info(f"[SILVER] tenant={tenant_id} {resultado}")
        return context


class StepProcessarChamadosGold(Step):
    """Gold: processa tabela final agregada."""

    def __init__(self):
        super().__init__("ProcessarChamadosGold")

    def execute(self, context: dict) -> dict:
        tenant_id = context["tenant_id"]
        
        resultado = processar_chamados_geral_gold()
        
        context["gold_resultado"] = resultado
        
        logger.info(f"[GOLD] tenant={tenant_id} {resultado}")
        return context


# ── Interface pública ─────────────────────────────────────────

def executar_pipeline_chamados(
    tenant_id: int = 1,
    aberto: str | None = None,
) -> dict:
    """
    Executa o pipeline completo Bronze → Silver → Gold
    para um tenant específico.
    
    Espelho do executar_pipeline_financeiro()
    
    Args:
        tenant_id: ID do tenant
        aberto: Data de abertura (filtro - ISO 8601)
        
    Returns:
        Dict com resultado da execução
    """
    
    # ✅ Cria pipeline exatamente como Financeiro
    pipeline = (
        Pipeline(f"ChamadosPipeline-tenant{tenant_id}")
        .add_step(StepExtrairChamados(
            tenant_id=tenant_id,
            aberto=aberto,
        ))
        .add_step(StepTransformarChamados())
        .add_step(StepProcessarChamadosGold())
    )

    return pipeline.run({"tenant_id": tenant_id})


def executar_todos_tenants(
    aberto: str | None = None,
) -> list[dict]:
    """
    Executa o pipeline para TODOS os tenants ativos.
    Usado pelo agendador (cron/systemd).
    
    Espelho do executar_todos_tenants() do Financeiro
    
    Args:
        aberto: Data de abertura (filtro)
        
    Returns:
        Lista com resultado de cada tenant
    """
    from repositories.tenant_repository import listar_tenants_ativos

    tenants = listar_tenants_ativos()
    resultados = []

    for t in tenants:
        logger.info(f"Iniciando pipeline para tenant: {t['nome']} (id={t['id']})")
        try:
            res = executar_pipeline_chamados(
                tenant_id=t["id"],
                aberto=aberto,
            )
            resultados.append({"tenant_id": t["id"], "status": "ok", **res})
        except Exception as e:
            logger.error(f"Erro no tenant {t['id']}: {e}")
            resultados.append({"tenant_id": t["id"], "status": "erro", "erro": str(e)})

    return resultados


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def _buscar_apoios_raw(tenant_id: int) -> list[dict]:
    """Busca registros de apoio da tabela raw"""
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT *
            FROM chamados_apoio_raw
            WHERE tenant_id = %s
            """,
            (tenant_id,)
        )
        rows = cursor.fetchall()
        logger.info(f"Apoios raw encontrados: {len(rows)}")
        return rows
    
    finally:
        cursor.close()
        conn.close()


def _buscar_etiquetas_raw(tenant_id: int) -> list[dict]:
    """Busca registros de etiqueta da tabela raw"""
    
    conn = connection_mysql()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT *
            FROM chamados_etiqueta_raw
            WHERE tenant_id = %s
            """,
            (tenant_id,)
        )
        rows = cursor.fetchall()
        logger.info(f"Etiquetas raw encontradas: {len(rows)}")
        return rows
    
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