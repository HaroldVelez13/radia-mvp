"""Vencimiento de derechos de peticion using habilmente for Colombian business days."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Set

import habilmente

from app.application.services.reglas_peticion import (
    EntidadUrgente,
    TipoPeticion,
    clasificar_peticion,
)


@dataclass
class ResultadoVencimiento:
    """Resultado del calculo de vencimiento de peticion."""
    fecha_recepcion: date
    fecha_inicio_plazo: date
    fecha_vencimiento: date
    plazo_dias_habiles: int
    tipo_peticion: str
    es_urgente: bool = False
    tutela_detectada: bool = False
    entidad_detectada: Optional[str] = None
    observaciones: str = ""


def _to_date(fecha_recepcion: date | datetime) -> date:
    """Convert datetime to date if needed."""
    if isinstance(fecha_recepcion, datetime):
        return fecha_recepcion.date()
    return fecha_recepcion


def calcular_vencimiento_simple(
    fecha_recepcion: date,
    dias_habiles: int,
) -> date:
    """
    Calculate deadline: next business day after receipt, then sum dias_habiles-1 business days.
    The -1 is because the first business day (fecha_inicio) counts as day 1.
    """
    fecha_inicio = habilmente.siguiente_dia_habil(_to_date(fecha_recepcion))
    return habilmente.sumar_dias_habiles(fecha_inicio, dias_habiles - 1)


def calcular_vencimiento_peticion(
    fecha_recepcion: date | datetime,
    tipo_peticion: Optional[str] = None,
    asunto: str = "",
    cuerpo: str = "",
    remitente: str = "",
) -> ResultadoVencimiento:
    """
    Calculate vencimiento for a derecho de peticion.

    If tipo_peticion is not provided, it is classified from asunto/cuerpo.
    Urgency is detected from tutela keywords and control entities.
    """
    fecha_rec = _to_date(fecha_recepcion)

    # Classify type if not explicit
    if tipo_peticion is None:
        clasificacion = clasificar_peticion(asunto or "", cuerpo, remitente)
        tipo_str = clasificacion.tipo.value
        plazo = clasificacion.plazo_dias_habiles
        es_urgente = clasificacion.es_urgente
        tutela_detectada = clasificacion.palabra_clave_tutela
        entidad = (
            clasificacion.entidad_detectada.value
            if clasificacion.entidad_detectada
            else None
        )
    else:
        tipo_str = tipo_peticion
        try:
            tipo_enum = TipoPeticion(tipo_peticion)
            plazo = tipo_enum.plazo_dias_habiles
        except ValueError:
            plazo = 15
        # Still check urgency from asunto/cuerpo/remitente
        clasificacion = clasificar_peticion(asunto or "", cuerpo, remitente)
        es_urgente = clasificacion.es_urgente
        tutela_detectada = clasificacion.palabra_clave_tutela
        entidad = (
            clasificacion.entidad_detectada.value
            if clasificacion.entidad_detectada
            else None
        )

    # Deadline calculation
    fecha_inicio = habilmente.siguiente_dia_habil(fecha_rec)
    fecha_venc = habilmente.sumar_dias_habiles(fecha_inicio, plazo - 1)

    # Observations
    observaciones = []
    if not habilmente.es_dia_habil(fecha_rec):
        observaciones.append(f"Fecha de recepcion {fecha_rec} no hábil, plazo inicia {fecha_inicio}")
    else:
        observaciones.append(f"Plazo inicia el dia siguiente: {fecha_inicio}")
    observaciones.append(f"Vencimiento: {plazo} dias habiles desde {fecha_inicio} -> {fecha_venc}")

    if es_urgente:
        urgente_parts = []
        if tutela_detectada:
            urgente_parts.append("tutela")
        if entidad:
            urgente_parts.append(entidad)
        observaciones.append(f"URGENTE: {', '.join(urgente_parts)}")

    return ResultadoVencimiento(
        fecha_recepcion=fecha_rec,
        fecha_inicio_plazo=fecha_inicio,
        fecha_vencimiento=fecha_venc,
        plazo_dias_habiles=plazo,
        tipo_peticion=tipo_str,
        es_urgente=es_urgente,
        tutela_detectada=tutela_detectada,
        entidad_detectada=entidad,
        observaciones="; ".join(observaciones),
    )


def es_dia_habil_colombia(fecha: date) -> bool:
    """Check if a date is a business day in Colombia (excludes weekends and holidays)."""
    return habilmente.es_dia_habil(fecha)


def obtener_festivos_colombia(year: int) -> Set[date]:
    """Return the set of Colombian holiday dates for a given year."""
    festivos = habilmente.fechas_festivas(year)
    return set(festivos)
