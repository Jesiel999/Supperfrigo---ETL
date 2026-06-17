import time
import logging

logger = logging.getLogger(__name__)


class Metrics:
    """Rastreia tempo total, registros processados e velocidade."""

    def __init__(self):
        self._start: float | None = None
        self._end:   float | None = None
        self.total_processados = 0
        self.total_inseridos   = 0
        self.total_atualizados = 0
        self.total_ignorados   = 0
        self.total_erros       = 0

    def start(self):
        self._start = time.time()

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
        """Registros por segundo."""
        if self.elapsed == 0:
            return 0.0
        return round(self.total_processados / self.elapsed, 2)

    def summary(self) -> dict:
        return {
            "tempo_total_segundos": self.elapsed,
            "velocidade_reg_por_segundo": self.velocidade,
            "total_processados": self.total_processados,
            "total_inseridos":   self.total_inseridos,
            "total_atualizados": self.total_atualizados,
            "total_ignorados":   self.total_ignorados,
            "total_erros":       self.total_erros,
        }

    def log_summary(self):
        s = self.summary()
        logger.info("=" * 50)
        logger.info("MÉTRICAS DO PIPELINE")
        for k, v in s.items():
            logger.info(f"  {k}: {v}")
        logger.info("=" * 50)
