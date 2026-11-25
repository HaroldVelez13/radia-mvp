"""Extractor de datos estructurados usando Ollama Qwen."""

from app.infrastructure.llm.ollama_client import OllamaClient


# Prompt para extracción de datos de factura
# Usamos llaves dobles para escapar las llaves del JSON en el template
EXTRACCION_FACTURA_PROMPT = """
Extrae los siguientes campos de esta factura y responde SOLO con JSON válido:
{{
  "nit": "string o null",
  "numero_factura": "string o null",
  "orden_compra": "string o null",
  "cuenta_bancaria": "string o null",
  "valor_total": "number o null"
}}

Reglas:
- NIT: solo dígitos, sin puntos ni guiones (ej: 900123456)
- numero_factura: formato de factura electrónica (ej: FE-3381, FV-12345)
- orden_compra: formato OC-YYYY-NNNN (ej: OC-2026-0412)
- cuenta_bancaria: número de cuenta bancaria colombiana (ej: 123456789012)
- valor_total: número decimal (ej: 1250000.00)

Si un campo no se encuentra, usa null.

Texto:
{texto}
"""


def _normalizar_nit(nit: str | None) -> str | None:
    """Normaliza NIT: solo dígitos."""
    if not nit:
        return None
    # Quitar puntos, guiones, espacios
    import re
    nit_limpio = re.sub(r"[^\d]", "", str(nit))
    return nit_limpio if nit_limpio else None


def _normalizar_numero_factura(num: str | None) -> str | None:
    """Normaliza número de factura: mayúsculas, sin espacios extra."""
    if not num:
        return None
    return str(num).strip().upper()


def _normalizar_orden_compra(oc: str | None) -> str | None:
    """Normaliza orden de compra: formato OC-YYYY-NNNN."""
    if not oc:
        return None
    oc_limpio = str(oc).strip().upper()
    # Si no tiene formato OC-YYYY-NNNN, devolver como viene
    import re
    if not re.match(r"^OC-\d{4}-\d{4}$", oc_limpio):
        # Intentar extraer solo los números si viene en formato raro
        return oc_limpio
    return oc_limpio


def _normalizar_cuenta_bancaria(cuenta: str | None) -> str | None:
    """Normaliza cuenta bancaria: solo dígitos."""
    if not cuenta:
        return None
    import re
    cuenta_limpia = re.sub(r"[^\d]", "", str(cuenta))
    return cuenta_limpia if cuenta_limpia else None


def _normalizar_valor_total(valor: str | float | int | None) -> float | None:
    """Normaliza valor total a float."""
    if valor is None:
        return None
    try:
        if isinstance(valor, (int, float)):
            return float(valor)
        
        v = str(valor).strip()
        # Formatos colombianos: 1.250.000, 1,250,000, 1250000, 1250000.00, 1250000,00
        # Si tiene coma y punto, asumir formato 1.250.000,00 o 1,250,000.00
        if "," in v and "." in v:
            # Verificar cuál es el separador decimal (el último)
            ultimo_punto = v.rfind(".")
            ultima_coma = v.rfind(",")
            if ultima_coma > ultimo_punto:
                # Coma es decimal: 1.250.000,00
                v = v.replace(".", "").replace(",", ".")
            else:
                # Punto es decimal: 1,250,000.00
                v = v.replace(",", "")
        elif "," in v:
            # Solo comas: podría ser 1,250,000 (miles) o 1250000,00 (decimal)
            partes = v.split(",")
            if len(partes[-1]) == 3 and len(partes) > 1:
                # Probablemente separador de miles: 1,250,000
                v = v.replace(",", "")
            else:
                # Probablemente decimal: 1250000,00
                v = v.replace(",", ".")
        elif "." in v:
            # Solo puntos: podría ser 1.250.000 (miles) o 1250000.00 (decimal)
            partes = v.split(".")
            if len(partes[-1]) == 3 and len(partes) > 1:
                # Probablemente separador de miles: 1.250.000
                v = v.replace(".", "")
            # else: ya es decimal con punto
        return float(v)
    except (ValueError, TypeError):
        return None


def extraer_datos_factura(texto: str) -> dict:
    """
    Extrae datos estructurados de una factura usando Ollama Qwen.

    Args:
        texto: Texto del documento (asunto + cuerpo + texto PDF si disponible).

    Returns:
        dict con keys: nit, numero_factura, orden_compra, cuenta_bancaria, valor_total
        Todos los valores normalizados según reglas colombianas.
    """
    if not texto or not texto.strip():
        return {
            "nit": None,
            "numero_factura": None,
            "orden_compra": None,
            "cuenta_bancaria": None,
            "valor_total": None,
        }

    client = OllamaClient()
    prompt = EXTRACCION_FACTURA_PROMPT.format(texto=texto[:8000])  # Limitar longitud
    resultado = client.chat_json(prompt)

    # Extraer y normalizar cada campo
    nit = _normalizar_nit(resultado.get("nit"))
    numero_factura = _normalizar_numero_factura(resultado.get("numero_factura"))
    orden_compra = _normalizar_orden_compra(resultado.get("orden_compra"))
    cuenta_bancaria = _normalizar_cuenta_bancaria(resultado.get("cuenta_bancaria"))
    valor_total = _normalizar_valor_total(resultado.get("valor_total"))

    return {
        "nit": nit,
        "numero_factura": numero_factura,
        "orden_compra": orden_compra,
        "cuenta_bancaria": cuenta_bancaria,
        "valor_total": valor_total,
    }


# Para compatibilidad futura: extractores de otros tipos
def extraer_datos_viatico(texto: str) -> dict:
    """Placeholder para extracción de viáticos (T3.3)."""
    return {
        "formato_valido": False,
        "firma_jefe": False,
        "fecha_viaje": None,
        "destino": None,
        "valor": None,
    }


def extraer_datos_peticion(texto: str) -> dict:
    """Placeholder para extracción de petición (T3.3)."""
    return {
        "tipo_peticion": None,  # general, copias, consulta, copias+otras
        "es_urgente": False,
        "motivo_urgente": None,
    }