import logging

from core.step import Step
from core.metrics import Metrics
from core.execution import ExecutionControl
from repositories.pipeline_execucao_repository import iniciar_execucao, finalizar_execucao

logger = logging.getLogger(__name__)


class Pipeline:

    def __init__(self, name: str):
        self.name = name

        self.steps: list[Step] = []

        self.metrics = Metrics()

        self.execution = ExecutionControl(name)

    def add_step(self, step: Step) -> "Pipeline":
        self.steps.append(step)

        return self

    def run(self, context: dict | None = None) -> dict:

        context = context or {}

        tenant_id = context.get("tenant_id")

        pipeline_offset_id = context.get(
            "pipeline_offset_id"
        )

        offset_inicial = context.get(
            "offset_inicial"
        )

        execucao_id = None

        self.metrics.start()
        self.execution.start()

        try:

            # -------------------------------------------------
            # REGISTRA INÍCIO DA EXECUÇÃO
            # -------------------------------------------------

            if (
                pipeline_offset_id is not None
                and tenant_id is not None
            ):

                execucao_id = iniciar_execucao(
                    pipeline_offset_id=pipeline_offset_id,
                    tenant_id=tenant_id,
                    offset_inicial=offset_inicial,
                )

                context["pipeline_execucao_id"] = execucao_id

                # logger.info(
                #    f"[PIPELINE] Execução registrada: "
                #    f"id={execucao_id}"
                # )

            # -------------------------------------------------
            # EXECUTA STEPS
            # -------------------------------------------------

            for step in self.steps:

                # logger.info(
                #    f"[PIPELINE] Executando step: "
                #    f"{step.name}"
                # )

                context = step.run(context)

                # ---------------------------------------------
                # COLETA RESULTADO DO STEP
                # ---------------------------------------------

                resultado = context.get(
                    self._resultado_key(step)
                )

                if isinstance(resultado, dict):
                    self.metrics.adicionar_resultado(
                        resultado
                    )

            # -------------------------------------------------
            # SUCESSO
            # -------------------------------------------------

            self.execution.success()

            return {
                "execution": self.execution.to_dict(),
                "metrics": self.metrics.summary(),
                "context": context,
            }

        except Exception as e:

            self.execution.fail(str(e))

            raise

        finally:

            # -------------------------------------------------
            # FINALIZA MÉTRICAS
            # -------------------------------------------------

            self.metrics.stop()

            # -------------------------------------------------
            # FINALIZA HISTÓRICO
            # -------------------------------------------------

            if execucao_id is not None:

                execution_data = (
                    self.execution.to_dict()
                )

                if (
                    execution_data["status"]
                    == "SUCCESS"
                ):
                    status = "CONCLUIDO"

                elif (
                    execution_data["status"]
                    == "CANCELLED"
                ):
                    status = "CANCELADO"

                else:
                    status = "ERRO"

                try:

                    finalizar_execucao(
                        execucao_id=execucao_id,
                        metrics=self.metrics,
                        status=status,
                        offset_final=context.get(
                            "offset_final"
                        ),
                        mensagem_erro=(
                            None
                            if status == "CONCLUIDO"
                            else execution_data.get(
                                "error_message"
                            )
                        ),
                    )

                except Exception as e:

                    logger.exception(
                        "[PIPELINE] Erro ao finalizar "
                        f"histórico da execução "
                        f"{execucao_id}: {e}"
                    )

            # -------------------------------------------------
            # LOG
            # -------------------------------------------------

            self.metrics.log_summary()

    @staticmethod
    def _resultado_key(step: Step) -> str:
        mapping = {
            "ExtrairEstoque": "bronze_estoque_resultado",
            "TransformarEstoque": "silver_estoque_resultado",
        }

        return mapping.get(
            step.name,
            f"{step.name.lower()}_resultado",
        )