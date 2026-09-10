import logging
import time

logger = logging.getLogger(__name__)


class Metrics:
    """Rastreia métricas de execução do pipeline."""

    def __init__(self):
        self._start: float | None = None
        self._end: float | None = None

        self.total_processados = 0
        self.total_inseridos = 0
        self.total_atualizados = 0
        self.total_ignorados = 0
        self.total_erros = 0

    def start(self):
        self._start = time.time()
        self._end = None

    def stop(self):
        self._end = time.time()

    @property
    def elapsed(self) -> float:
        if self._start is None:
            return 0.0

        end = self._end or time.time()

        return round(end - self._start, 2)

    @property
    def velocidade(self) -> float:
        if self.elapsed <= 0:
            return 0.0

        return round(
            self.total_processados / self.elapsed,
            2,
        )

    def adicionar(
        self,
        processados: int = 0,
        inseridos: int = 0,
        atualizados: int = 0,
        ignorados: int = 0,
        erros: int = 0,
    ):
        """
        Adiciona métricas de um step à execução.
        """

        self.total_processados += processados
        self.total_inseridos += inseridos
        self.total_atualizados += atualizados
        self.total_ignorados += ignorados
        self.total_erros += erros

    def adicionar_resultado(self, resultado: dict | None):
        """
        Extrai métricas de um resultado de step.

        Aceita diferentes nomes para facilitar integração
        com os resultados existentes.
        """

        if not resultado:
            return

        self.adicionar(
            processados=resultado.get(
                "total_processados",
                resultado.get("processados", 0),
            ),
            inseridos=resultado.get(
                "total_inseridos",
                resultado.get("inseridos", 0),
            ),
            atualizados=resultado.get(
                "total_atualizados",
                resultado.get("atualizados", 0),
            ),
            ignorados=resultado.get(
                "total_ignorados",
                resultado.get("ignorados", 0),
            ),
            erros=resultado.get(
                "total_erros",
                resultado.get("erros", 0),
            ),
        )

    def summary(self) -> dict:
        return {
            "tempo_total_segundos": self.elapsed,
            "velocidade_reg_por_segundo": self.velocidade,
            "total_processados": self.total_processados,
            "total_inseridos": self.total_inseridos,
            "total_atualizados": self.total_atualizados,
            "total_ignorados": self.total_ignorados,
            "total_erros": self.total_erros,
        }

    def log_summary(self):
        summary = self.summary()

        #logger.info("=" * 50)
        #logger.info("MÉTRICAS DO PIPELINE")

        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

        #logger.info("=" * 50)