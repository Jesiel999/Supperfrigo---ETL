from apscheduler.schedulers.background import BackgroundScheduler

from run_pipeline_sances_financeiro import executar_sances_diario
from run_pipeline_sances_financeiro_total import executar_sances_total
from run_pipeline_sults import executar_sults
from run_pipeline_sances_pessoa import executar_sances_pessoa

from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger

scheduler = BackgroundScheduler()

def job_sances_financeiro_diario():
    job_sances_financeiro_diario()

def job_sances_financeiro_total():
    job_sances_financeiro_total()

def job_sances_pessoa():
    executar_sances_pessoa()

def job_sults():
    executar_sults()

def iniciar_scheduler():

     # DIÁRIO -> 30/30 min, 07h–19h, seg a sáb
    trigger_diario = OrTrigger([
        CronTrigger(day_of_week="mon-sat", hour="7-18", minute="0,30"),
        CronTrigger(day_of_week="mon-sat", hour="19", minute="0"),
    ])
    scheduler.add_job(
        job_sances_financeiro_diario,
        trigger_diario,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        # next_run_time=datetime.now(),
        id="etl_financeiro_diario",
    )

    # TOTAL -> 30/30 min, 19h–07h, todos os dias
    trigger_total = CronTrigger(hour="19-23,0-6", minute="0,30")
    scheduler.add_job(
        job_sances_financeiro_total,
        trigger_total,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        # next_run_time=datetime.now(),
        id="etl_financeiro_total",
    )

    scheduler.add_job(
        job_sults,
        "interval",
        minutes=3000,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        next_run_time=datetime.now(),
        id="etl_chamados",
    )

    scheduler.start()
    
    # PESSOA -> 2x ao dia, às 12h e às 19h
    # trigger_pessoa = CronTrigger(hour="12,19", minute="0")
    trigger_pessoa = CronTrigger(minute="0,30")
    scheduler.add_job(
        job_sances_pessoa,
        trigger_pessoa,
        max_instances=1,
        misfire_grace_time=300,
        next_run_time=datetime.now(),
        coalesce=True,
        replace_existing=True,
        id="etl_pessoa_sances",
    )


def parar_scheduler():
    scheduler.shutdown(wait=False)