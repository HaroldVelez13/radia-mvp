import os
from pathlib import Path
import openpyxl

from app.infrastructure.excel.libro import generar_consecutivo, escribir_libro
from app.infrastructure.eml.parser import parse_eml


def procesar_bandeja():
    """Process one EML from the bandeja end-to-end.

    Steps:
    1. List .eml files from data/bandeja
    2. Parse the first one
    3. Generate consecutive via libro
    4. Write to Excel libro
    5. Return result dict
    """
    # 1. List .eml files
    bandeja_dir = Path("/data/bandeja")
    eml_files = sorted(bandeja_dir.glob("*.eml"))

    if not eml_files:
        return {"message": "No .eml files in bandeja", "processed": False}

    # 2. Parse the first EML file
    eml_path = eml_files[0]
    radicado_data = parse_eml(str(eml_path))

    # 3. Generate consecutive
    consecutivo = generar_consecutivo()

    # 4. Build radicado dict and write to Excel
    radicado = {
        "consecutivo": consecutivo,
        "fecha": radicado_data.get("fecha"),
        "remitente": radicado_data.get("remitente"),
        "nit_documento": radicado_data.get("nit"),
        "tipo_documental": radicado_data.get("tipo_documental", "Factura"),
        "asunto": radicado_data.get("asunto"),
        "no_documento": radicado_data.get("no_documento"),
        "valor_total": radicado_data.get("valor_total"),
        "dependencia": radicado_data.get("dependencia", ""),
        "fecha_vencimiento": radicado_data.get("vencimiento"),
        "estado": radicado_data.get("estado", "En trámite"),
        "observaciones": radicado_data.get("observaciones", ""),
    }

    escribir_libro(radicado)

    # 5. Return result
    return {
        "message": f"EML processed: {eml_path.name}",
        "processed": True,
        "consecutivo": consecutivo,
        "radicado": radicado,
    }