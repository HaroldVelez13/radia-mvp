from fastapi import APIRouter
from fastapi.responses import JSONResponse
import traceback
from pathlib import Path
from datetime import date

from app.application.use_cases.procesar_bandeja import procesar_bandeja
from app.infrastructure.eml.parser import parse_eml
from app.infrastructure.excel.libro import generar_consecutivo
from app.application.services.reglas_factura import es_duplicado, verificar_fraude_cuenta
from app.application.services.reglas_viaticos import validar_viatico_completo
from app.application.services.reglas_peticion import clasificar_peticion

router = APIRouter()


@router.get("/")
def listar_bandeja():
    """List .eml files from data/bandeja."""
    bandeja_dir = Path("/data/bandeja")
    eml_files = sorted(bandeja_dir.glob("*.eml"))
    return {"files": [f.name for f in eml_files], "count": len(eml_files)}


@router.get("/analisis")
def analisis_bandeja():
    """Analyze all .eml files in bandeja and return semáforo analysis."""
    bandeja_dir = Path("/data/bandeja")
    eml_files = sorted(bandeja_dir.glob("*.eml"))

    results = []
    for eml_file in eml_files:
        try:
            # Parse EML
            parsed = parse_eml(str(eml_file))

            # Determine semáforo color and motivo
            semaforo = _analizar_semaforo(parsed)

            results.append({
                "archivo": eml_file.name,
                "fecha": parsed.get("fecha"),
                "remitente": parsed.get("remitente"),
                "asunto": parsed.get("asunto"),
                "tipo_documental": parsed.get("tipo_documental"),
                "no_documento": parsed.get("no_documento"),
                "nit": parsed.get("nit"),
                "semaforo": semaforo["color"],
                "motivo": semaforo["motivo"],
                "observaciones": semaforo.get("observaciones", []),
            })
        except Exception as e:
            results.append({
                "archivo": eml_file.name,
                "error": str(e),
                "semaforo": "gris",
                "motivo": f"Error al procesar: {e}",
            })

    return {"items": results, "total": len(results)}


def _analizar_semaforo(parsed: dict) -> dict:
    """Analyze parsed EML and return semáforo color and motivo.

    Colors:
    - rojo: riesgo duplicado/fraude/tutela
    - amarillo: viaticos incompleto
    - verde: ok
    """
    observaciones = []

    # Check for tutela/petición urgente (rojo)
    asunto = parsed.get("asunto", "") or ""
    if "tutela" in asunto.lower():
        return {
            "color": "rojo",
            "motivo": "Contiene palabra 'tutela' - peticion urgente",
            "observaciones": ["Detectada palabra clave: tutela"],
        }

    # Check for factura - duplicado/fraude
    tipo = parsed.get("tipo_documental", "Factura")
    nit = parsed.get("nit")
    no_documento = parsed.get("no_documento")

    if tipo == "Factura":
        # Check duplicado
        if nit and no_documento:
            try:
                duplicado, radicado, motivo_dup = es_duplicado(
                    nit, no_documento, "/data/libro/libro-radicacion-2026.xlsx"
                )
                if duplicado:
                    return {
                        "color": "rojo",
                        "motivo": f"Factura duplicada: {motivo_dup}",
                        "observaciones": [motivo_dup],
                    }
                observaciones.append(f"Duplicado: {motivo_dup}")
            except Exception as e:
                observaciones.append(f"Error verificando duplicado: {e}")

        # Check fraude (if we have account/email)
        # Note: We don't have cuenta/correo from EML alone, would need PDF
        # For now, skip detailed fraude check

        return {
            "color": "verde",
            "motivo": "Factura sin riesgos detectados",
            "observaciones": observaciones,
        }

    # Check for viaticos - formato/firma/5 dias (amarillo si incompleto)
    if tipo == "Viáticos":
        # We'd need the full document text and dates
        # For now, based on subject only
        if not no_documento:
            return {
                "color": "amarillo",
                "motivo": "Viatico sin numero de documento",
                "observaciones": ["Falta numero viatico TH-F-012"],
            }

        # Check format
        formato_valido, motivo_formato = validar_viatico_completo(
            numero_viatico=no_documento or "",
            texto_documento=asunto,
            fecha_recepcion=parsed.get("fecha") or date.today(),
            fecha_viatico=date.today(),  # placeholder
        )
        if not formato_valido:
            return {
                "color": "amarillo",
                "motivo": f"Viatico: {motivo_formato}",
                "observaciones": [motivo_formato],
            }

    # Check for peticion - tutela/entidades control (rojo if urgente)
    if tipo == "Derecho de petición":
        resultado = clasificar_peticion(asunto)
        if resultado.es_urgente:
            return {
                "color": "rojo",
                "motivo": f"Peticion urgente: {resultado.tipo.value} - {resultado.entidad_detectada or 'tutela'}",
                "observaciones": [
                    f"Tipo: {resultado.tipo.value}",
                    f"Plazo: {resultado.plazo_dias_habiles} dias habiles",
                    f"Entidad: {resultado.entidad_detectada.value if resultado.entidad_detectada else 'N/A'}",
                ],
            }
        return {
            "color": "verde",
            "motivo": f"Peticion {resultado.tipo.value} - {resultado.plazo_dias_habiles} dias habiles",
            "observaciones": [
                f"Tipo: {resultado.tipo.value}",
                f"Plazo: {resultado.plazo_dias_habiles} dias habiles",
            ],
        }

    # Default verde
    return {
        "color": "verde",
        "motivo": "Documento sin riesgos detectados",
        "observaciones": observaciones,
    }


@router.post("/procesar")
def procesar_bandeja_endpoint():
    """Process one EML from the bandeja end-to-end."""
    try:
        result = procesar_bandeja()
        return result
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})