"""Business rules for viaticos (travel expenses) validation: TH-F-012 format, firma, 5-dias rule."""
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Tuple


@dataclass
class ResultadoViatico:
    """Result of viatico validation."""
    es_valido: bool
    motivo: str
    observaciones: list[str] = field(default_factory=list)


# Regex pattern for TH-F-012 viatico number format: VI-YYYY-NNNN or VIATICO-YYYY-NNNNN
FORMATO_VIATICO_PATTERN = re.compile(
    r"^(VI|VIATICO|VIÁTICO)\s*[-]\s*\d{4}\s*[-]\s*\d{3,5}$", re.IGNORECASE
)

FIRMA_PATTERNS = [
    re.compile(r"firma\s*:\s*\w+", re.IGNORECASE),
    re.compile(r"firmado\s+por\s+\w+", re.IGNORECASE),
    re.compile(r"aprobado\s+por\s+\w+", re.IGNORECASE),
    re.compile(r"autorizado\s+por\s+\w+", re.IGNORECASE),
]


def _normalizar_texto(texto: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r"\s+", " ", texto.strip().lower())


def validar_formato_viatico(numero_viatico: str) -> Tuple[bool, str]:
    """
    Validate viatico number format.
    Expected: VI-YYYY-NNNN or VIATICO-YYYY-NNNNN (TH-F-012 format).
    """
    if not numero_viatico:
        return False, "Numero de viatico vacio"

    if FORMATO_VIATICO_PATTERN.match(numero_viatico.strip()):
        return True, "Formato valido TH-F-012"

    return False, (
        f"Formato invalido: '{numero_viatico}'. "
        "Se espera VI-YYYY-NNNN o VIATICO-YYYY-NNNNN"
    )


def validar_firma(texto: str) -> Tuple[bool, str]:
    """
    Detect if a signature/approval is present in the viatico document text.
    """
    if not texto or not texto.strip():
        return False, "Sin firma jefe, devolver"

    texto_normalizado = _normalizar_texto(texto)
    for pattern in FIRMA_PATTERNS:
        if pattern.search(texto_normalizado):
            return True, "Firma presente"

    return False, "Sin firma jefe, devolver"


def validar_antiguedad_5_dias(
    fecha_recepcion: date | datetime,
    fecha_viatico: date | datetime,
) -> Tuple[bool, str]:
    """
    Validate that the viatico is submitted at least 5 business days before the trip.
    Returns (es_valido, motivo).
    """
    if isinstance(fecha_recepcion, datetime):
        fecha_recepcion = fecha_recepcion.date()
    if isinstance(fecha_viatico, datetime):
        fecha_viatico = fecha_viatico.date()

    if fecha_viatico <= fecha_recepcion:
        return False, "Fecha de recepcion antes del viatico (extemporaneo)"

    delta_dias = (fecha_viatico - fecha_recepcion).days
    if delta_dias < 5:
        return False, f"Viatico extemporaneo: solo {delta_dias} dias antes del viaje (se requieren 5)"

    return True, f"Antiguedad valida: {delta_dias} dias habiles antes del viaje"


def validar_viatico_completo(
    numero_viatico: str,
    texto_documento: str,
    fecha_recepcion: date | datetime,
    fecha_viatico: date | datetime,
) -> ResultadoViatico:
    """
    Complete viatico validation: formato TH-F-012, firma, 5-dias rule.
    """
    observaciones: list[str] = []

    # 1. Formato TH-F-012
    formato_valido, motivo_formato = validar_formato_viatico(numero_viatico)
    observaciones.append(f"Formato: {motivo_formato}")
    if not formato_valido:
        return ResultadoViatico(
            es_valido=False,
            motivo="Viatico invalido: formato TH-F-012 incorrecto",
            observaciones=observaciones,
        )

    # 2. Firma jefe
    firma_valida, motivo_firma = validar_firma(texto_documento)
    observaciones.append(f"Firma: {motivo_firma}")
    if not firma_valida:
        return ResultadoViatico(
            es_valido=False,
            motivo="Viatico invalido: falta firma del jefe inmediato",
            observaciones=observaciones,
        )

    # 3. 5-dias rule
    antiguedad_valida, motivo_antiguedad = validar_antiguedad_5_dias(fecha_recepcion, fecha_viatico)
    observaciones.append(f"Antiguedad: {motivo_antiguedad}")
    if not antiguedad_valida:
        return ResultadoViatico(
            es_valido=False,
            motivo="Viatico extemporaneo: se requieren al menos 5 dias antes del viaje",
            observaciones=observaciones,
        )

    return ResultadoViatico(
        es_valido=True,
        motivo="Viatico valido: formato TH-F-012, firma y anticipacion correctas",
        observaciones=observaciones,
    )


# Keep the original placeholder function for compatibility
def aplicar_reglas_viaticos(
    datos,
    dias_habiles_para_viaje: int,
):
    """Original placeholder: T2.4 viaticos rules."""
    from app.domain.enums import Dependencia, EstadoRadicado

    if not getattr(datos, "formato_viatico", False):
        return Dependencia.NO_RADICAR, EstadoRadicado.NO_RADICADO, "Sin formato TH-F-012, devolver"
    if not getattr(datos, "firma_jefe", False):
        return Dependencia.NO_RADICAR, EstadoRadicado.NO_RADICADO, "Sin firma jefe, devolver"
    if dias_habiles_para_viaje < 5:
        return Dependencia.TALENTO_HUMANO, EstadoRadicado.RADICADO, "Viatico extemporaneo (<5 dias habiles), requiere autorizacion especial"
    return Dependencia.TALENTO_HUMANO, EstadoRadicado.RADICADO, "Viatico OK"
