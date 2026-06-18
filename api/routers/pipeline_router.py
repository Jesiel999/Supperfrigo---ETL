from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pipelines.financeiro_pipeline import executar_pipeline_financeiro
from auth.router import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class PipelineRequest(BaseModel):
    data_baixa_inicial: Optional[str] = None
    data_baixa_final:   Optional[str] = None
    data_vencimento_inicial: Optional[str] = None
    data_vencimento_final:   Optional[str] = None


_ultimo_resultado: dict = {}


def _run_pipeline(req: PipelineRequest):
    global _ultimo_resultado
    try:
        _ultimo_resultado = executar_pipeline_financeiro(
            data_baixa_inicial=req.data_baixa_inicial,
            data_baixa_final=req.data_baixa_final,
            data_vencimento_inicial=req.data_vencimento_inicial,
            data_vencimento_final=req.data_vencimento_final,
        )
    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        _ultimo_resultado = {"error": str(e)}


@router.post("/executar")
def executar_pipeline(
    req: PipelineRequest,
    background_tasks: BackgroundTasks,
    _user: str = Depends(get_current_user),
):
    """
    Dispara o pipeline financeiro em background.
    Aceita filtro opcional por data de baixa.
    """
    background_tasks.add_task(_run_pipeline, req)
    return {"status": "Pipeline iniciado em background", "filtros": req.dict()}


@router.get("/status")
def status_pipeline(_user: str = Depends(get_current_user)):
    """Retorna o resultado da última execução do pipeline."""
    return _ultimo_resultado or {"status": "Nenhuma execução registrada"}


@router.post("/executar/sync")
def executar_pipeline_sync(
    req: PipelineRequest,
    _user: str = Depends(get_current_user),
):
    """
    Executa o pipeline de forma síncrona e retorna o resultado completo.
    Use apenas para testes / execuções manuais.
    """
    try:
        resultado = executar_pipeline_financeiro(
            data_baixa_inicial=req.data_baixa_inicial,
            data_baixa_final=req.data_baixa_final,
            data_vencimento_inicial=req.data_vencimento_inicial,
            data_vencimento_final=req.data_vencimento_final,
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
