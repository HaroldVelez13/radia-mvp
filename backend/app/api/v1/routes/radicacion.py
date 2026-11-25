from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def listar_radicados():
    return {"radicados": []}

@router.get("/{radicado_id}")
def obtener_radicado(radicado_id: str):
    return {"radicado": radicado_id, "por": "implementar"}
