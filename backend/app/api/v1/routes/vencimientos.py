from fastapi import APIRouter

router = APIRouter()

@router.get("/semana")
def vencimientos_semana():
    # Para Claudia
    return {"vence_esta_semana": [], "por_implementar": True}
