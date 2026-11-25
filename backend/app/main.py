from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.v1.api import api_router

setup_logging()

app = FastAPI(
    title="RADIA - Radicacion Asistida",
    description="MVP local para TNHI - Terminales Andinas Carga",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "service": "radia-api", "version": "0.1.0"}

@app.get("/")
def root():
    return {"message": "RADIA API - Ver /docs"}
