"""Clasificador de documentos: fast path (Jev-Style) + slow path (Ollama Qwen).

Tipos soportados: factura, viatico, derecho_peticion, oficio_control,
queja_transporte, cotizacion, publicidad, desconocido.
"""
from app.infrastructure.llm.ollama_client import OllamaClient
from app.infrastructure.llm.jev_style_client import JevStyleClient
from app.domain.enums import TipoDocumento


# Prompt para clasificación con Ollama (slow path)
# Usamos llaves dobles para escapar las llaves del JSON en el template
CLASIFICACION_PROMPT = """
Clasifica este documento en uno de: factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad
Responde SOLO JSON: {{\"tipo\": \"...\", \"confianza\": 0.0-1.0, \"motivo\": \"...\"}}
Texto: {texto}
"""


# Keywords para detectar derecho de petición implícito
PETICION_IMPLICITA_KEYWORDS = [
    "solicito",
    "les pido que me informen",
    "derecho de peticion",
    "peticion",
    "requiero",
    "exijo",
    "pido informacion",
]


def detectar_peticion_implicita(texto: str) -> bool:
    """Detecta si el texto contiene indicios de derecho de petición implícito."""
    texto_lower = texto.lower()
    return any(keyword in texto_lower for keyword in PETICION_IMPLICITA_KEYWORDS)


def _obtener_tipo_maximo(probabilidades: dict) -> tuple[str, float]:
    """Obtiene el tipo con mayor probabilidad y su valor."""
    if not probabilidades:
        return "desconocido", 0.0
    max_tipo = max(probabilidades, key=probabilidades.get)
    max_conf = probabilidades[max_tipo]
    return max_tipo, max_conf


def _generar_motivo_desde_probabilidades(tipo: str, probs: dict, es_fallback: bool = False) -> str:
    """Genera un motivo explicativo basado en las probabilidades."""
    top3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
    partes = [f"{t}:{p:.2f}" for t, p in top3]
    base = f"Clasificación {'Ollama' if es_fallback else 'Jev-Style'}: {tipo} ({', '.join(partes)})"
    return base


def clasificar_documento(texto: str) -> dict:
    """
    Clasifica un documento usando fast path (Jev-Style) + slow path (Ollama).

    Args:
        texto: Texto del documento a clasificar (asunto + cuerpo).

    Returns:
        dict con keys: tipo (TipoDocumento), confianza (float), motivo (str), fuente (str)
    """
    if not texto or not texto.strip():
        return {
            "tipo": TipoDocumento.DESCONOCIDO,
            "confianza": 0.0,
            "motivo": "Texto vacío",
            "fuente": "none",
        }

    # --- Fast path: Jev-Style ---
    jev_client = JevStyleClient()
    probabilidades = jev_client.classify(texto)

    tipo_fast, conf_fast = _obtener_tipo_maximo(probabilidades)

    # Si detectamos petición implícita y el tipo fast no es derecho_peticion,
    # forzamos revisión con slow path
    if detectar_peticion_implicita(texto) and tipo_fast != "derecho_peticion":
        # Forzar slow path para validar
        conf_fast = 0.0

    # Si confianza alta (>= 0.8), devolvemos fast path
    if conf_fast >= 0.8:
        return {
            "tipo": TipoDocumento(tipo_fast),
            "confianza": round(conf_fast, 4),
            "motivo": _generar_motivo_desde_probabilidades(tipo_fast, probabilidades, es_fallback=False),
            "fuente": "jev_style",
        }

    # --- Slow path: Ollama Qwen ---
    ollama_client = OllamaClient()
    prompt = CLASIFICACION_PROMPT.format(texto=texto[:4000])  # Limitar longitud
    resultado = ollama_client.chat_json(prompt)

    tipo_slow = resultado.get("tipo", "desconocido")
    conf_slow = float(resultado.get("confianza", 0.0))
    motivo_slow = resultado.get("motivo", "Sin motivo")

    # Validar que el tipo devuelto es válido
    try:
        tipo_enum = TipoDocumento(tipo_slow)
    except ValueError:
        tipo_enum = TipoDocumento.DESCONOCIDO
        conf_slow = 0.0
        motivo_slow = f"Tipo inválido devuelto por LLM: {tipo_slow}"

    # Si el slow path también falla (confianza baja), usar fast path como respaldo
    if conf_slow < 0.5 and conf_fast > 0:
        return {
            "tipo": TipoDocumento(tipo_fast),
            "confianza": round(conf_fast, 4),
            "motivo": _generar_motivo_desde_probabilidades(tipo_fast, probabilidades, es_fallback=False) + " (fallback fast path)",
            "fuente": "jev_style_fallback",
        }

    return {
        "tipo": tipo_enum,
        "confianza": round(conf_slow, 4),
        "motivo": motivo_slow,
        "fuente": "ollama",
    }


# Para compatibilidad con tests existentes
def clasificar_peticion(texto: str) -> str:
    """Wrapper simple que devuelve solo el tipo como string (legacy)."""
    resultado = clasificar_documento(texto)
    return resultado["tipo"].value