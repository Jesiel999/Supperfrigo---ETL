from fastapi import FastAPI
from api.routers import pipeline_router, financeiro_router, dashboard_router
from auth.router import router as auth_router
from config.logging import setup_logging
from fastapi.middleware.cors import CORSMiddleware

setup_logging()

app = FastAPI(
    title="ETL API",
    description="API para execução e monitoramento do pipeline ETL",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,       prefix="/auth",      tags=["Auth"])
app.include_router(pipeline_router.router,   prefix="/pipeline",  tags=["Pipeline"])
app.include_router(financeiro_router.router, prefix="/financeiro", tags=["Financeiro"])
app.include_router(dashboard_router.router,  prefix="/dashboard",  tags=["Dashboard"])


@app.get("/")
def root():
    return {"status": "ETL API online"}
