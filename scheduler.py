from apscheduler.schedulers.background import BackgroundScheduler
from run_pipeline_sances import executar_sances
from run_pipeline_sults import executar_sults
from datetime import datetime

scheduler = BackgroundScheduler()

def job_sances():
    executar_sances()

def job_sults():
    executar_sults()

def iniciar_scheduler():

    scheduler.add_job(
        job_sances,
        "interval",
        minutes=30,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        next_run_time=datetime.now(),
        id="etl_financeiro",
    )

    scheduler.add_job(
        job_sults,
        "interval",
        minutes=30,
        max_instances=1,
        misfire_grace_time=300,
        coalesce=True,
        replace_existing=True,
        next_run_time=datetime.now(),
        id="etl_chamados",
    )

    scheduler.start()


def parar_scheduler():
    scheduler.shutdown(wait=False)