from fastapi import FastAPI
from api.routers import pipeline_router, financeiro_router, usuarios_router, permissoes_router, empresas_router, menu_router
from auth.router import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from scheduler import iniciar_scheduler, parar_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):

    iniciar_scheduler()

    yield

    parar_scheduler()

app = FastAPI(
    title="ETL API",
    description="API para execucao e monitoramento do pipeline ETL",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/auth",  tags=["Auth"])
app.include_router(menu_router.router, prefix="", tags=["Menu"])
app.include_router(pipeline_router.router,   prefix="/pipeline",  tags=["Pipeline"])
app.include_router(financeiro_router.router, prefix="/financeiro", tags=["Financeiro"])
app.include_router(usuarios_router.router,  prefix="/usuarios",  tags=["Usuarios"])
app.include_router(permissoes_router.router, prefix="/permissoes", tags=["Permissoes"])
app.include_router(empresas_router.router, prefix="/empresas", tags=["Empresas"])

@app.get("/")
def root():
    return {"status": "ETL API online"}
