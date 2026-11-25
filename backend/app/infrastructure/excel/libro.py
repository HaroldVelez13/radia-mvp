import openpyxl
from pathlib import Path

def generar_consecutivo(ultimo: int) -> str:
    return f"TAC-2026-ER-{ultimo+1:05d}"

def escribir_libro(path: str, radicado: dict):
    # T4.2
    pass
