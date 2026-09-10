from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Step(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: dict) -> dict:
        pass

    def run(self, context: dict) -> dict:
        #logger.info("[STEP] Iniciando: {self.name}")

        try:
            result = self.execute(context)

            #logger.info("[STEP] Concluído: {self.name}")

            return result

        except Exception as e:
            #logger.error("[STEP] Erro em {self.name}: {e}")

            raise