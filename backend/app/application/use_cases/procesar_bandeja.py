import os
from pathlib import Path
import openpyxl

from app.infrastructure.excel.libro import generar_consecutivo, escribir_libro
from app.infrastructure.eml.parser import parse_eml
from app.infrastructure.llm.jev_style_client import JevStyleClient
from app.domain.enums import EstadoRadicado
from app.application.services.reglas_factura import es_duplicado, verificar_fraude_cuenta


def _clasificar_confianza(texto: str) -> tuple[str, float]:
    """Clasifica el texto y retorna (tipo_top, confianza_max)."""
    client = JevStyleClient()
    probs = client.classify(texto)
    if not probs:
        return "desconocido", 0.0
    tipo_top = max(probs, key=probs.get)
    confianza = probs[tipo_top]
    return tipo_top, confianza


def _necesita_revision_humana(radicado_data: dict, parsed_full: dict) -> tuple[bool, str]:
    """
    Determina si el radicado necesita revisión humana.

    Returns (necesita_revision, motivo).
    """
    # 1. Confianza del clasificador < 0.6
    texto_para_clasificar = f"{radicado_data.get('asunto', '')} {radicado_data.get('tipo_documental', '')}"
    tipo, confianza = _clasificar_confianza(texto_para_clasificar)
    if confianza < 0.6:
        return True, f"Baja confianza en clasificación ({tipo}: {confianza:.2f} < 0.60)"

    # 2. Fraude detectado (rojo en semáforo)
    tipo_doc = radicado_data.get("tipo_documental", "Factura")
    if tipo_doc == "Factura":
        nit = radicado_data.get("nit")
        no_documento = radicado_data.get("no_documento")
        if nit and no_documento:
            # Check duplicado
            duplicado, _, motivo_dup = es_duplicado(
                nit, no_documento, "/data/libro/libro-radicacion-2026.xlsx"
            )
            if duplicado:
                return True, f"Fraude/Duplicado detectado: {motivo_dup}"

            # Note: Fraude cuenta/correo would need PDF extraction (OCR)
            # For now, we flag based on duplicado only

    # 3. Tutela / petición urgente (rojo en semáforo)
    asunto = radicado_data.get("asunto", "") or ""
    if "tutela" in asunto.lower():
        return True, "Contiene palabra 'tutela' - petición urgente"

    return False, ""


def procesar_bandeja():
    """Process one EML from the bandeja end-to-end.

    Steps:
    1. List .eml files from data/bandeja
    2. Parse the first one
    3. Generate consecutive via libro
    4. Check if needs human review (confianza < 0.6 or rojo fraude)
    5. Write to Excel libro with appropriate estado
    6. Return result dict
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

    # 4. Check if needs human review
    necesita_revision, motivo_revision = _necesita_revision_humana(radicado_data, radicado_data)

    # 5. Determine estado
    if necesita_revision:
        estado = EstadoRadicado.REVISION_HUMANA.value
        observaciones = f"PENDIENTE REVISIÓN: {motivo_revision}"
    else:
        estado = radicado_data.get("estado", "En trámite")
        observaciones = radicado_data.get("observaciones", "")

    # 6. Build radicado dict and write to Excel
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
        "estado": estado,
        "observaciones": observaciones,
    }

    escribir_libro(radicado)

    # 7. Return result
    return {
        "message": f"EML processed: {eml_path.name}",
        "processed": True,
        "consecutivo": consecutivo,
        "radicado": radicado,
        "necesita_revision": necesita_revision,
        "motivo_revision": motivo_revision if necesita_revision else None,
    }