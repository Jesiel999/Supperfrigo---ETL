from contextlib import asynccontextmanager
from fastapi import FastAPI

from scheduler import iniciar_scheduler, parar_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_scheduler()
    try:
        yield
    finally:
        parar_scheduler()


app = FastAPI(lifespan=lifespan)