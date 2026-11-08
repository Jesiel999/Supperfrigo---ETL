import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

# ATENÇÃO: os run_pipeline_* NÃO são mais importados aqui.
# Cada job roda em um processo próprio (veja _rodar), que importa o que precisa.
# Resultado: o processo do scheduler fica leve e, quando o job termina,
# o Windows devolve TODA a memória daquele job.

logger = logging.getLogger("scheduler")

DIR_ETL = os.path.dirname(os.path.abspath(__file__))

# Quantos pipelines podem rodar ao mesmo tempo.
# Se a máquina ainda ficar pesada, troque para 1.
MAX_PIPELINES_SIMULTANEOS = 2
_VAGAS = threading.Semaphore(MAX_PIPELINES_SIMULTANEOS)


def _rodar(modulo: str, funcao: str, timeout: int) -> None:
    """
    Executa `modulo.funcao()` em um processo Python separado.
    - espera uma vaga livre (limita a memória usada ao mesmo tempo);
    - se passar de `timeout` segundos, o processo é encerrado
      (o offset já fica salvo, a próxima execução continua de onde parou).
    """
    with _VAGAS:
        inicio = time.time()
        logger.info("[%s] iniciando", funcao)

        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

        try:
            resultado = subprocess.run(
                [sys.executable, "-c", f"from {modulo} import {funcao}; {funcao}()"],
                cwd=DIR_ETL,
                env=env,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            logger.error("[%s] encerrado por timeout de %ss", funcao, timeout)
            return

        duracao = time.time() - inicio

        if resultado.returncode != 0:
            logger.error(
                "[%s] terminou com erro (código %s) em %.0fs",
                funcao, resultado.returncode, duracao,
            )
        else:
            logger.info("[%s] concluído em %.0fs", funcao, duracao)


def _em(segundos: int) -> datetime:
    """Primeira execução ao subir o scheduler, escalonada para não
    disparar tudo no mesmo segundo."""
    return datetime.now() + timedelta(seconds=segundos)


scheduler = BackgroundScheduler(
    executors={"default": ThreadPoolExecutor(8)}
)


# ── JOBS (cada um só chama _rodar) ───────────────────────────
# timeout em segundos; os de 30 em 30 min ficam abaixo de 30 min.

def job_sances_pos_venda():
    _rodar("run_pipeline_sances_pos_venda", "executar_sances_pos_venda", 1500)

def job_sances_estoque():
    _rodar("run_pipeline_sances_estoque", "executar_sances_estoque", 1500)

def job_sances_estoque_veiculos():
    _rodar("run_pipeline_sances_estoque_veiculos", "executar_sances_estoque_veiculos", 1500)

def job_sances_estoque_veiculos_completo():
    _rodar("run_pipeline_sances_estoque_veiculos", "executar_sances_estoque_veiculos_completo", 7200)

def job_sances_financeiro_diario():
    _rodar("run_pipeline_sances_financeiro", "executar_sances_diario", 1500)

def job_sances_financeiro_total():
    _rodar("run_pipeline_sances_financeiro_total", "executar_sances_total", 1500)

def job_pessoa():
    _rodar("run_pipeline_pessoa", "executar_pessoa", 3000)

def job_sults_chamados():
    _rodar("run_pipeline_sults", "executar_sults_chamados", 1500)

def job_econnect_telemetria():
    _rodar("run_pipeline_econnect_telemetria", "executar_econnect_telemetria", 110)


def iniciar_scheduler():

    # Os minutos foram ESCALONADOS para os pipelines não começarem juntos:
    #   :00/:30 pós-venda | :05/:35 estoque | :10/:40 veículos
    #   :15/:45 financeiro diário | :20/:50 financeiro total | :25 pessoa

    # SANCES PÓS-VENDA -> 30 em 30 minutos
    scheduler.add_job(
        job_sances_pos_venda,
        CronTrigger(minute="0,30"),
        max_instances=1,
        misfire_grace_time=300,
        next_run_time=_em(0),
        coalesce=True,
        replace_existing=True,
        id="etl_sances_pos_venda",
    )

    # SANCES ESTOQUE (peças) -> 30 em 30 minutos
    scheduler.add_job(
        job_sances_estoque,
        CronTrigger(minute="5,35"),
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=_em(60),
        coalesce=True,
        replace_existing=True,
        id="etl_estoque_sances",
    )

    # ESTOQUE VEÍCULOS (incremental) -> 30 em 30 minutos
    scheduler.add_job(
        job_sances_estoque_veiculos,
        CronTrigger(minute="10,40"),
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=_em(120),
        coalesce=True,
        replace_existing=True,
        id="etl_estoque_veiculos_sances",
    )

    # ESTOQUE VEÍCULOS (completo) -> 1x por dia às 03:15
    scheduler.add_job(
        job_sances_estoque_veiculos_completo,
        CronTrigger(hour="3", minute="15"),
        max_instances=1,
        misfire_grace_time=1800,
        # next_run_time=_em(0),   # descomente só na carga inicial
        coalesce=True,
        replace_existing=True,
        id="etl_estoque_veiculos_sances_completo",
    )

    # SANCES FINANCEIRO DIÁRIO -> 30/30 min, 07h–19h, seg a sáb
    trigger_diario = OrTrigger([
        CronTrigger(day_of_week="mon-sat", hour="7-18", minute="15,45"),
        CronTrigger(day_of_week="mon-sat", hour="19", minute="15"),
    ])
    scheduler.add_job(
        job_sances_financeiro_diario,
        trigger_diario,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        id="etl_financeiro_diario",
    )

    # SANCES FINANCEIRO TOTAL -> 30/30 min, 19h–07h, todos os dias
    scheduler.add_job(
        job_sances_financeiro_total,
        CronTrigger(hour="19-23,0-6", minute="20,50"),
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=_em(180),
        coalesce=True,
        replace_existing=True,
        id="etl_financeiro_total",
    )

    # PESSOA -> 2x ao dia, às 12h25 e 19h25
    scheduler.add_job(
        job_pessoa,
        CronTrigger(hour="12,19", minute="25"),
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        id="etl_pessoa_sances",
    )

    # CHAMADOS (desativado)
    # scheduler.add_job(
    #     job_sults_chamados,
    #     CronTrigger(minute="0,30"),
    #     max_instances=1,
    #     misfire_grace_time=300,
    #     next_run_time=_em(240),
    #     coalesce=True,
    #     replace_existing=True,
    #     id="etl_chamados",
    # )

    # TELEMETRIA (desativado) -> 2 em 2 minutos
    # scheduler.add_job(
    #     job_econnect_telemetria,
    #     CronTrigger(minute="*/2"),
    #     max_instances=1,
    #     misfire_grace_time=120,
    #     next_run_time=_em(0),
    #     coalesce=True,
    #     replace_existing=True,
    #     id="etl_telemetria_econnect",
    # )

    scheduler.start()


def parar_scheduler():
    scheduler.shutdown(wait=False)