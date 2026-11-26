import openpyxl
from pathlib import Path
from datetime import datetime

# In container, data is mounted at /data
EXCEL_PATH = Path("/data/libro/libro-radicacion-2026.xlsx")
SHEET_NAME = "Radicación 2026"


def generar_consecutivo() -> str:
    """Read the Excel sheet to find the max Consecutivo number, return the next one.

    Format: TAC-2026-ER-xxxxx (5 digits)
    """
    wb = openpyxl.load_workbook(str(EXCEL_PATH))
    ws = wb[SHEET_NAME]

    max_num = 0
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1, values_only=True):
        val = row[0]
        if val and isinstance(val, str) and val.startswith("TAC-2026-ER-"):
            try:
                num = int(val.split("-")[-1])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    return f"TAC-2026-ER-{max_num + 1:05d}"


def escribir_libro(radicado: dict):
    """Append a radicado row to the Excel sheet.

    Expected radicado keys matching columns Radicacion2026:
    - consecutivo
    - fecha
    - remitente
    - nit_documento
    - tipo_documental
    - asunto
    - no_documento
    - valor_total
    - dependencia
    - fecha_vencimiento
    - estado
    - observaciones
    """
    wb = openpyxl.load_workbook(str(EXCEL_PATH))
    ws = wb[SHEET_NAME]

    def strip_tz(val):
        if isinstance(val, datetime) and val.tzinfo is not None:
            return val.replace(tzinfo=None)
        return val

    # Append row in the order of columns: A=Radicado, B=Fecha, C=Remitente, D=NIT, E=Tipo, F=Asunto,
    # G=No documento, H=Valor total, I=Dependencia, J=Fecha vencimiento, K=Estado, L=Observaciones
    row_data = [
        radicado.get("consecutivo"),
        strip_tz(radicado.get("fecha")),
        radicado.get("remitente"),
        radicado.get("nit_documento"),
        radicado.get("tipo_documental"),
        radicado.get("asunto"),
        radicado.get("no_documento"),
        radicado.get("valor_total"),
        radicado.get("dependencia"),
        strip_tz(radicado.get("fecha_vencimiento")),
        radicado.get("estado"),
        radicado.get("observaciones"),
    ]

    ws.append(row_data)
    wb.save(str(EXCEL_PATH))