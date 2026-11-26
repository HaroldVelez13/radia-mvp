from fastapi import APIRouter
from pathlib import Path
from datetime import date, datetime
import openpyxl

from app.application.services.reglas_peticion import clasificar_peticion

router = APIRouter()


@router.get("/")
def vencimientos():
    """Get all peticiones with dias_habiles remaining, ordered by urgency.

    For Claudia - shows peticiones that need attention this week.
    """
    # Read from libro de radicacion
    libro_path = Path("/data/libro/libro-radicacion-2026.xlsx")
    if not libro_path.exists():
        return {"items": [], "total": 0, "message": "Libro no encontrado"}

    try:
        wb = openpyxl.load_workbook(libro_path, data_only=True)
        ws = wb[wb.sheetnames[0]]  # First sheet

        items = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row is None:
                continue

            radicado = row[0] if len(row) > 0 else None
            fecha_recibido = row[1] if len(row) > 1 else None
            remitente = row[2] if len(row) > 2 else None
            nit = row[3] if len(row) > 3 else None
            tipo_documental = row[4] if len(row) > 4 else None
            asunto = row[5] if len(row) > 5 else None
            no_documento = row[6] if len(row) > 6 else None
            valor_total = row[7] if len(row) > 7 else None
            dependencia = row[8] if len(row) > 8 else None
            fecha_vencimiento = row[9] if len(row) > 9 else None
            estado = row[10] if len(row) > 10 else None
            observaciones = row[11] if len(row) > 11 else None

            # Only process peticiones (derecho de peticion) - handle accent
            tipo_str = str(tipo_documental).lower()
            if tipo_documental and ("peticion" in tipo_str or "petición" in tipo_str):
                # Classify to get plazo
                resultado = clasificar_peticion(asunto or "")

                # Calculate dias_habiles remaining
                dias_habiles = _calcular_dias_habiles_restantes(fecha_recibido, resultado.plazo_dias_habiles)

                # Urgencia level
                urgencia = "normal"
                if resultado.es_urgente or resultado.palabra_clave_tutela:
                    urgencia = "urgente"
                elif dias_habiles <= 3:
                    urgencia = "critica"
                elif dias_habiles <= 7:
                    urgencia = "alta"

                items.append({
                    "radicado": radicado,
                    "fecha_recibido": str(fecha_recibido) if fecha_recibido else None,
                    "remitente": remitente,
                    "asunto": asunto,
                    "tipo_documental": tipo_documental,
                    "plazo_dias_habiles": resultado.plazo_dias_habiles,
                    "dias_habiles_restantes": dias_habiles,
                    "es_urgente": resultado.es_urgente,
                    "entidad_detectada": resultado.entidad_detectada.value if resultado.entidad_detectada else None,
                    "palabra_clave_tutela": resultado.palabra_clave_tutela,
                    "dependencia": dependencia,
                    "estado": estado,
                    "urgencia": urgencia,
                })

        # Sort by urgencia (critica > alta > urgente > normal) then by dias_habiles
        urgencia_order = {"critica": 0, "alta": 1, "urgente": 2, "normal": 3}
        items.sort(key=lambda x: (urgencia_order.get(x["urgencia"], 4), x["dias_habiles_restantes"]))

        return {"items": items, "total": len(items)}

    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}


def _calcular_dias_habiles_restantes(fecha_recibido, plazo_dias_habiles: int) -> int:
    """Calculate remaining business days from fecha_recibido + plazo."""
    if not fecha_recibido:
        return 999

    # Convert to date if datetime or string
    if isinstance(fecha_recibido, datetime):
        fecha_recibido = fecha_recibido.date()
    elif isinstance(fecha_recibido, str):
        try:
            fecha_recibido = datetime.strptime(fecha_recibido[:10], "%Y-%m-%d").date()
        except ValueError:
            return 999

    # Calculate vencimiento date (adding business days)
    vencimiento = _sumar_dias_habiles(fecha_recibido, plazo_dias_habiles)

    # Calculate remaining business days from today
    today = date.today()
    if vencimiento < today:
        return -1  # Vencido

    return _contar_dias_habiles(today, vencimiento)


def _sumar_dias_habiles(fecha_inicio: date, dias_habiles: int) -> date:
    """Add business days to a date."""
    from datetime import timedelta

    current = fecha_inicio
    added = 0
    while added < dias_habiles:
        current += timedelta(days=1)
        # Monday=0, Sunday=6
        if current.weekday() < 5:  # Mon-Fri
            added += 1
    return current


def _contar_dias_habiles(inicio: date, fin: date) -> int:
    """Count business days between two dates (inclusive of start, exclusive of end)."""
    if inicio >= fin:
        return 0

    from datetime import timedelta
    count = 0
    current = inicio
    while current < fin:
        if current.weekday() < 5:
            count += 1
        current = current + timedelta(days=1)
    return count


@router.get("/semana")
def vencimientos_semana():
    """Legacy endpoint - peticiones que vencen esta semana."""
    result = vencimientos()
    items = [item for item in result.get("items", []) if item.get("dias_habiles_restantes", 999) <= 7]
    return {"items": items, "total": len(items)}