import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    SUCCESS   = "SUCCESS"
    FAILED    = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionControl:
    """Controla o estado de execução de um pipeline."""

    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self.status        = ExecutionStatus.PENDING
        self.error_message: str | None = None

    def start(self):
        self.status = ExecutionStatus.RUNNING
        logger.info(f"[EXECUTION] Pipeline '{self.pipeline_name}' INICIADO")

    def success(self):
        self.status = ExecutionStatus.SUCCESS
        logger.info(f"[EXECUTION] Pipeline '{self.pipeline_name}' CONCLUÍDO COM SUCESSO")

    def fail(self, error: str):
        self.status        = ExecutionStatus.FAILED
        self.error_message = error
        logger.error(f"[EXECUTION] Pipeline '{self.pipeline_name}' FALHOU: {error}")

    def to_dict(self) -> dict:
        return {
            "pipeline":      self.pipeline_name,
            "status":        self.status,
            "error_message": self.error_message,
        }
