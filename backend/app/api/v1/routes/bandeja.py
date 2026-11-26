from fastapi import APIRouter
from fastapi.responses import JSONResponse
import traceback

from app.application.use_cases.procesar_bandeja import procesar_bandeja

router = APIRouter()


@router.get("/")
def listar_bandeja():
    """List .eml files from data/bandeja."""
    from pathlib import Path

    bandeja_dir = Path("/data/bandeja")
    eml_files = sorted(bandeja_dir.glob("*.eml"))
    return {"files": [f.name for f in eml_files], "count": len(eml_files)}


@router.post("/procesar")
def procesar_bandeja_endpoint():
    """Process one EML from the bandeja end-to-end.

    Steps:
    1. Find first .eml file
    2. Parse with OCR/LLM
    3. Generate consecutive
    4. Write to Excel libro
    5. Return result
    """
    try:
        result = procesar_bandeja()
        return result
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})