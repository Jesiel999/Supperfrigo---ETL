from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Step(ABC):
    """Classe base. Todo step do pipeline herda dela."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """Executa o step e retorna o contexto atualizado."""
        ...

    def run(self, context: dict) -> dict:
        logger.info(f"[STEP] Iniciando: {self.name}")
        try:
            result = self.execute(context)
            logger.info(f"[STEP] Concluído: {self.name}")
            return result
        except Exception as e:
            logger.error(f"[STEP] Erro em {self.name}: {e}")
            raise
