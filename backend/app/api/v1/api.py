from fastapi import APIRouter
from app.api.v1.routes import health, bandeja, radicacion, vencimientos

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(bandeja.router, prefix="/bandeja", tags=["bandeja"])
api_router.include_router(radicacion.router, prefix="/radicados", tags=["radicados"])
api_router.include_router(vencimientos.router, prefix="/vencimientos", tags=["vencimientos"])
