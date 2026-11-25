from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def listar_bandeja():
    # T1.1: implementar lectura real de data/bandeja
    return {"message": "Bandeja - por implementar T1.1", "count": 0}

@router.post("/procesar")
def procesar_bandeja():
    # T4.3: procesar bandeja completa
    return {"message": "Procesar bandeja - por implementar"}
