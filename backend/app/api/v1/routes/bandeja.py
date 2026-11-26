from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import traceback
from pathlib import Path
from datetime import date

from app.application.use_cases.procesar_bandeja import procesar_bandeja
from app.infrastructure.eml.parser import parse_eml
from app.infrastructure.excel.libro import generar_consecutivo, escribir_libro
from app.application.services.reglas_factura import es_duplicado, verificar_fraude_cuenta
from app.application.services.reglas_viaticos import validar_viatico_completo
from app.application.services.reglas_peticion import clasificar_peticion
from app.domain.enums import EstadoRadicado

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


@router.get("/pendientes")
def listar_pendientes():
    """Get all radicados with estado = 'revision_humana' from libro."""
    try:
        from app.infrastructure.excel.libro import EXCEL_PATH, SHEET_NAME
        import openpyxl

        wb = openpyxl.load_workbook(str(EXCEL_PATH), data_only=True)
        ws = wb[SHEET_NAME]

        # Columns: A=Radicado(0), B=Fecha(1), C=Remitente(2), D=NIT(3), E=Tipo(4),
        # F=Asunto(5), G=No documento(6), H=Valor(7), I=Dependencia(8),
        # J=Vencimiento(9), K=Estado(10), L=Observaciones(11)
        pendientes = []
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
            if row is None or len(row) < 11:
                continue
            estado = row[10] if len(row) > 10 else None
            if estado == EstadoRadicado.REVISION_HUMANA.value:
                pendientes.append({
                    "consecutivo": row[0],
                    "fecha": row[1],
                    "remitente": row[2],
                    "nit_documento": row[3],
                    "tipo_documental": row[4],
                    "asunto": row[5],
                    "no_documento": row[6],
                    "valor_total": row[7],
                    "dependencia": row[8],
                    "fecha_vencimiento": row[9],
                    "estado": row[10],
                    "observaciones": row[11],
                })

        return {"items": pendientes, "total": len(pendientes)}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/revisar/{consecutivo}")
def revisar_pendiente(consecutivo: str, accion: dict):
    """Aprobar o rechazar un radicado pendiente de revisión.

    Body: {"accion": "aprobar" | "rechazar"}
    """
    try:
        accion_val = accion.get("accion")
        if accion_val not in ("aprobar", "rechazar"):
            raise HTTPException(status_code=400, detail="Acción debe ser 'aprobar' o 'rechazar'")

        from app.infrastructure.excel.libro import EXCEL_PATH, SHEET_NAME
        import openpyxl

        wb = openpyxl.load_workbook(str(EXCEL_PATH))
        ws = wb[SHEET_NAME]

        # Find row with matching consecutivo (column A)
        row_idx = None
        for idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1, values_only=True), start=2):
            if row[0] == consecutivo:
                row_idx = idx
                break

        if row_idx is None:
            raise HTTPException(status_code=404, detail=f"Radicado {consecutivo} no encontrado")

        # Verify it's in revision_humana state
        estado_actual = ws.cell(row=row_idx, column=11).value  # Column K
        if estado_actual != EstadoRadicado.REVISION_HUMANA.value:
            raise HTTPException(status_code=400, detail=f"Radicado no está en revisión humana (estado actual: {estado_actual})")

        # Update estado and observaciones
        if accion_val == "aprobar":
            nuevo_estado = EstadoRadicado.RADICADO.value
            obs_extra = "APROBADO por revisión humana"
        else:
            nuevo_estado = EstadoRadicado.NO_RADICADO.value
            obs_extra = "RECHAZADO por revisión humana"

        ws.cell(row=row_idx, column=11, value=nuevo_estado)  # Estado
        obs_actual = ws.cell(row=row_idx, column=12).value or ""  # Observaciones
        ws.cell(row=row_idx, column=12, value=f"{obs_actual} | {obs_extra}".strip(" |"))

        wb.save(str(EXCEL_PATH))

        return {
            "message": f"Radicado {consecutivo} {accion_val}",
            "consecutivo": consecutivo,
            "nuevo_estado": nuevo_estado,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})