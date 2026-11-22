
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scheduler import iniciar_scheduler, parar_scheduler


# ==========================================================
# CONFIGURACAO DE LOG
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("bi.etl")


# ==========================================================
# CICLO DE VIDA DA APLICACAO
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("========================================")
    logger.info("INICIANDO SERVICO ETL")
    logger.info("========================================")

    try:
        iniciar_scheduler()

        logger.info("Agendador ETL inicializado com sucesso.")

        yield

    except Exception:
        logger.exception("Erro durante a inicializacao ou execucao do ETL.")
        raise

    finally:
        logger.info("Encerrando servico ETL...")

        try:
            parar_scheduler()
            logger.info("Agendador encerrado com sucesso.")

        except Exception:
            logger.exception("Erro ao encerrar o agendador.")

        logger.info("Servico ETL finalizado.")


# ==========================================================
# APLICACAO FASTAPI
# ==========================================================

app = FastAPI(
    title="BI - ETL",
    description="Serviço de integração e processamento de dados.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health():
    return {
        "status": "online",
        "service": "bi-etl"
    }
