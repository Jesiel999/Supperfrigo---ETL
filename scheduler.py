from apscheduler.schedulers.background import BackgroundScheduler

from run_pipeline_sances_financeiro import executar_sances_diario
from run_pipeline_sances_financeiro_total import executar_sances_total
from run_pipeline_sults import executar_sults_chamados
from run_pipeline_pessoa import executar_pessoa
from run_pipeline_sances_estoque import executar_sances_estoque
from run_pipeline_sances_pos_venda import executar_sances_pos_venda
from run_pipeline_econnect_telemetria import executar_econnect_telemetria

from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

scheduler = BackgroundScheduler(
    executors={"default": ThreadPoolExecutor(10)} # WORKERS EXECUTANDO SIMULTANEAMENTE
)

def job_sances_financeiro_diario():
    executar_sances_diario()

def job_sances_financeiro_total():
    executar_sances_total()

def job_sances_pos_venda():
    executar_sances_pos_venda()

def job_pessoa():
    executar_pessoa()

def job_sances_estoque():
    executar_sances_estoque()

def job_econnect_telemetria():
    executar_econnect_telemetria()

def job_sults_chamados():
    executar_sults_chamados()

def iniciar_scheduler():

    # SANCES POS VENDA -> 30 em 30 minutos
    trigger_pos_venda = CronTrigger(minute="0,30")
    scheduler.add_job(
        job_sances_pos_venda,
        trigger_pos_venda,
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=datetime.now(),
        coalesce=True,
        replace_existing=True,
        id="etl_sances_pos_venda",
    )

    # SANCES FINANCEIRO DIÁRIO -> 30/30 min, 07h–19h, seg a sáb
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
        next_run_time=datetime.now(), 
        id="etl_financeiro_diario",
    )

    # SANCES FINANCEIRO TOTAL -> 30/30 min, 19h–07h, todos os dias
    trigger_total = CronTrigger(hour="19-23,0-6", minute="0,30")
    scheduler.add_job(
        job_sances_financeiro_total,
        trigger_total,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        next_run_time=datetime.now(),
        id="etl_financeiro_total",
    )

    # CHAMADOS -> 30/30 min, todos os dias
    trigger_chamados = CronTrigger(minute="0,30")
    scheduler.add_job(
        job_sults_chamados,
        trigger_chamados,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        # next_run_time=datetime.now(),
        id="etl_chamados",
    )
    
    # PESSOA -> 2x ao dia, às 12h e às 19h
    # trigger_pessoa = CronTrigger(hour="12,19", minute="0")
    trigger_pessoa = CronTrigger(minute="0,30")
    scheduler.add_job(
        job_pessoa,
        trigger_pessoa,
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=datetime.now(),
        coalesce=True,
        replace_existing=True,
        id="etl_pessoa_sances",
    )

    # ESTOQUE -> 30 em 30 minutos
    trigger_estoque = CronTrigger(minute="0,30")
    scheduler.add_job(
        job_sances_estoque,
        trigger_estoque,
        max_instances=1,
        misfire_grace_time=300,
        # next_run_time=datetime.now(),
        coalesce=True,
        replace_existing=True,
        id="etl_estoque_sances",
    )
    
    # TELEMETRIA -> 2 em 2 minuto
    trigger_telemetria = CronTrigger(minute="*/2") 
    scheduler.add_job(
        job_econnect_telemetria,
        trigger_telemetria,
        max_instances=1,
        misfire_grace_time=120,
        next_run_time=datetime.now(),
        coalesce=True,
        replace_existing=True,
        id="etl_telemetria_econnect",
    )

    scheduler.start()

def parar_scheduler():
    scheduler.shutdown(wait=False)