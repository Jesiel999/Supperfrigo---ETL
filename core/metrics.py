
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class Metrics:
    """Centraliza métricas de execução do pipeline ETL."""

    def __init__(
        self,
        pipeline: str | None = None,
        camada: str | None = None,
    ):
        self.pipeline = pipeline
        self.camada = camada

        self.reset()

    def reset(self):
        """Reinicia as métricas da execução."""

        self._start: float | None = None
        self._end: float | None = None

        self.total_processados = 0
        self.total_inseridos = 0
        self.total_atualizados = 0
        self.total_ignorados = 0
        self.total_erros = 0

    def start(self):
        self._start = time.perf_counter()
        self._end = None

    def stop(self):
        if self._start is not None:
            self._end = time.perf_counter()

    @property
    def elapsed(self) -> float:
        if self._start is None:
            return 0.0

        end = self._end or time.perf_counter()

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
        """Acumula métricas de uma etapa."""

        self.total_processados += processados
        self.total_inseridos += inseridos
        self.total_atualizados += atualizados
        self.total_ignorados += ignorados
        self.total_erros += erros

    @staticmethod
    def _obter(
        resultado: dict,
        chave: str,
        chave_alternativa: str,
    ) -> int:
        valor = resultado.get(
            chave,
            resultado.get(chave_alternativa, 0),
        )

        return int(valor or 0)

    def adicionar_resultado(self, resultado: dict | None):
        """Extrai métricas de um resultado de etapa."""

        if not resultado:
            return

        self.adicionar(
            processados=self._obter(
                resultado, "total_processados", "processados"
            ),
            inseridos=self._obter(
                resultado, "total_inseridos", "inseridos"
            ),
            atualizados=self._obter(
                resultado, "total_atualizados", "atualizados"
            ),
            ignorados=self._obter(
                resultado, "total_ignorados", "ignorados"
            ),
            erros=self._obter(
                resultado, "total_erros", "erros"
            ),
        )

    def summary(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "camada": self.camada,
            "tempo_total_segundos": self.elapsed,
            "velocidade_reg_por_segundo": self.velocidade,
            "total_processados": self.total_processados,
            "total_inseridos": self.total_inseridos,
            "total_atualizados": self.total_atualizados,
            "total_ignorados": self.total_ignorados,
            "total_erros": self.total_erros,
        }

    def log_summary(self, logger_execucao=None):
        """Registra o resumo consolidado."""

        log = logger_execucao or logger
        resumo = self.summary()

        log.info("=" * 60)
        log.info(
            "[ETL] RESUMO DA EXECUÇÃO | pipeline=%s | camada=%s",
            self.pipeline,
            self.camada,
        )

        for chave, valor in resumo.items():
            if chave not in ("pipeline", "camada"):
                log.info("%s: %s", chave, valor)

        log.info("=" * 60)


def log_resultado(
    nome: str,
    resultado: dict | None,
    logger_execucao: logging.Logger | None = None,
):
    """Registra o resultado individual de uma etapa."""

    log = logger_execucao or logger

    if not resultado:
        log.warning(
            "[ETL] Nenhum resultado recebido | etapa=%s",
            nome,
        )
        return

    log.info(
        "[ETL] RESULTADO DA ETAPA | etapa=%s",
        nome,
    )

    metricas = {
        "processados": ("processados", "total_processados"),
        "inseridos": ("inseridos", "total_inseridos"),
        "atualizados": ("atualizados", "total_atualizados"),
        "ignorados": ("ignorados", "total_ignorados"),
        "erros": ("erros", "total_erros"),
    }

    for nome_metrica, chaves in metricas.items():
        valor = resultado.get(
            chaves[0],
            resultado.get(chaves[1], 0),
        )

        log.info("  %s: %s", nome_metrica, valor)
