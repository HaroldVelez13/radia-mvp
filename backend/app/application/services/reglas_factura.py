"""Business rules for factura: duplicate detection and fraud verification."""
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import openpyxl

from app.domain.entities.documento import DatosExtraidos
from app.domain.enums import Dependencia, EstadoRadicado


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_nit(nit: Optional[str]) -> str:
    """Normalize NIT: remove dots, dashes, spaces; uppercase."""
    if not nit:
        return ""
    return re.sub(r"[\.\-\s]", "", nit.strip()).upper()


def _normalize_numero(numero: Optional[str]) -> str:
    """Normalize factura numero: strip and uppercase."""
    if not numero:
        return ""
    return numero.strip().upper()


def _normalize_cuenta(cuenta: Optional[str]) -> str:
    """Normalize bank account: remove dots, dashes, spaces."""
    if not cuenta:
        return ""
    return re.sub(r"[\.\-\s]", "", cuenta.strip())


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def es_duplicado(
    nit: str,
    numero_factura: str,
    libro_path: Path | str,
) -> Tuple[bool, Optional[str], str]:
    """
    Detect if a factura (NIT + numero) already exists in the libro de radicacion.

    Returns (es_duplicado, radicado, motivo).
    """
    nit_norm = _normalize_nit(nit)
    numero_norm = _normalize_numero(numero_factura)

    if not nit_norm:
        return False, None, "NIT vacío"
    if not numero_norm:
        return False, None, "Número de factura vacío"

    libro_path = Path(libro_path)
    if not libro_path.exists():
        return False, None, "Archivo libro no encontrado"

    try:
        wb = openpyxl.load_workbook(libro_path, data_only=True)
    except Exception:
        return False, None, "Error leyendo libro de radicacion"

    sheet_name = wb.sheetnames[0]
    ws = wb[sheet_name]

    # Columns: A=Radicado(0), D=NIT/Documento(3), G=No. documento(6)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row is None:
            continue
        radicado = row[0] if len(row) > 0 else None
        nit_libro = row[3] if len(row) > 3 else None
        numero_libro = row[6] if len(row) > 6 else None

        if nit_libro is None or numero_libro is None:
            continue

        if (
            _normalize_nit(str(nit_libro)) == nit_norm
            and _normalize_numero(str(numero_libro)) == numero_norm
        ):
            return True, str(radicado), f"Duplicado: NIT {nit} + numero {numero_factura} ya radicado como {radicado}"

    return False, None, f"No existe factura con NIT {nit} y numero {numero_factura} en libro"


# ---------------------------------------------------------------------------
# Fraud verification (returns plain 3-tuple for test compatibility)
# ---------------------------------------------------------------------------

def verificar_fraude_cuenta(
    nit: str,
    cuenta_bancaria: str,
    correo: str,
    maestro_path: Path | str,
) -> Tuple[bool, str, Dependencia]:
    """
    Verify if bank account and email match the maestro proveedores for the given NIT.

    Returns (es_fraude, motivo, dependencia) where dependencia is a Dependencia enum.
    """
    maestro_path = Path(maestro_path)
    if not maestro_path.exists():
        return False, "Archivo maestro no encontrado", Dependencia.JURIDICA

    nit_norm = _normalize_nit(nit)
    cuenta_norm = _normalize_cuenta(cuenta_bancaria)
    correo_norm = correo.strip().lower() if correo else ""

    proveedor_encontrado = False
    proveedor_activo = False
    cuenta_maestro = ""
    correo_maestro = ""

    try:
        with open(maestro_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_nit = _normalize_nit(row.get("nit", ""))
                if row_nit == nit_norm:
                    proveedor_encontrado = True
                    estado = (row.get("estado", "") or "").strip().upper()
                    proveedor_activo = estado == "ACTIVO"
                    cuenta_maestro = _normalize_cuenta(row.get("numero_cuenta", ""))
                    correo_maestro = (row.get("correo_facturacion", "") or "").strip().lower()
                    break
    except Exception:
        return False, "Error leyendo maestro de proveedores", Dependencia.JURIDICA

    if not proveedor_encontrado:
        return False, "NIT no encontrado en maestro", Dependencia.JURIDICA

    if not proveedor_activo:
        return True, "Proveedor inactivo (Vigilancia Técnica)", Dependencia.JURIDICA

    # Skip checks if factura fields are empty
    if cuenta_norm:
        if cuenta_norm != cuenta_maestro:
            return True, "Cuenta no coincide con maestro", Dependencia.JURIDICA

    if correo_norm:
        if correo_norm != correo_maestro:
            return True, "Correo no coincide con maestro", Dependencia.JURIDICA

    return False, "OK: cuenta y correo coinciden con maestro", Dependencia.CUENTAS_POR_PAGAR


def verificar_fraude(
    nit: str,
    cuenta_bancaria: str,
    correo: str,
    maestro_path: Path | str | None = None,
) -> Tuple[bool, str, Dependencia]:
    """
    Convenience wrapper with default maestro path.
    """
    if maestro_path is None:
        maestro_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "maestro" / "maestro-proveedores.csv"
    return verificar_fraude_cuenta(nit, cuenta_bancaria, correo, maestro_path)


# ---------------------------------------------------------------------------
# Full factura rules (placeholder from original)
# ---------------------------------------------------------------------------

def aplicar_reglas_factura(
    datos: DatosExtraidos,
    proveedor_existe: bool,
    es_duplicado_flag: bool,
    cuenta_coincide: bool,
    correo_raro: bool,
):
    """T2.2 y T2.3: aplicar reglas de factura."""
    if es_duplicado_flag:
        return Dependencia.NO_RADICAR, EstadoRadicado.DUPLICADO, "Factura ya radicada NIT+numero en libro"
    if not cuenta_coincide or correo_raro:
        return Dependencia.CLAUDIA_HERRERA, EstadoRadicado.FRAUDE, "Cuenta bancaria no coincide con maestro o correo sospechoso"
    if not proveedor_existe:
        return Dependencia.COMPRAS, EstadoRadicado.RADICADO, "Proveedor no existe en maestro"
    if not datos.orden_compra:
        return Dependencia.COMPRAS, EstadoRadicado.RADICADO, "Factura sin OC, requiere aval Compras"
    return Dependencia.CUENTAS_POR_PAGAR, EstadoRadicado.RADICADO, "Factura con OC, va a pago"
