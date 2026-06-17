import logging
from core.step import Step
from core.metrics import Metrics
from core.execution import ExecutionControl, ExecutionStatus

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Orquestra steps em sequência.
    Controla erros, tempo e métricas por etapa.
    """

    def __init__(self, name: str):
        self.name      = name
        self.steps:    list[Step] = []
        self.metrics   = Metrics()
        self.execution = ExecutionControl(name)

    def add_step(self, step: Step) -> "Pipeline":
        self.steps.append(step)
        return self

    def run(self, context: dict | None = None) -> dict:
        context = context or {}
        self.metrics.start()
        self.execution.start()

        try:
            for step in self.steps:
                context = step.run(context)

            self.execution.success()

        except Exception as e:
            self.execution.fail(str(e))
            raise

        finally:
            self.metrics.stop()
            self.metrics.log_summary()

        return {
            "execution": self.execution.to_dict(),
            "metrics":   self.metrics.summary(),
            "context":   context,
        }
