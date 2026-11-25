"""Business rules for derecho de peticion: classification, urgency, and deadlines."""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# Module-level patterns (can't be inside Enum class)
_ENTIDAD_PATTERNS = {
    "contraloria": [re.compile(r"contralor[ií]a", re.IGNORECASE)],
    "procuraduria": [re.compile(r"procuradur[ií]a", re.IGNORECASE)],
    "personeria": [re.compile(r"personer[ií]a", re.IGNORECASE)],
    "juzgado": [re.compile(r"juzgado", re.IGNORECASE)],
}

# Ordered list for deterministic entity selection
_ENTIDAD_ORDER = ["contraloria", "procuraduria", "personeria", "juzgado"]


class TipoPeticion(str, Enum):
    """Tipos de derecho de peticion con plazos en dias habiles (Colombian law)."""
    GENERAL = "general"
    COPIAS = "copias"
    CONSULTA = "consulta"
    COPIAS_OTRAS = "copias_otras"

    @property
    def plazo_dias_habiles(self) -> int:
        mapping = {
            TipoPeticion.GENERAL: 15,
            TipoPeticion.COPIAS: 10,
            TipoPeticion.CONSULTA: 30,
            TipoPeticion.COPIAS_OTRAS: 15,
        }
        return mapping[self]


class EntidadUrgente(str, Enum):
    """Entidades de control que hacen una peticion urgente."""
    CONTRALORIA = "contraloria"
    PROCURADURIA = "procuraduria"
    PERSONERIA = "personeria"
    JUZGADO = "juzgado"

    @classmethod
    def detectar_en_texto(cls, texto: str) -> set:
        """Detect which urgent entities appear in texto (accent-insensitive)."""
        if not texto:
            return set()
        detectadas: set = set()
        for entidad_value in _ENTIDAD_ORDER:
            for pat in _ENTIDAD_PATTERNS[entidad_value]:
                if pat.search(texto):
                    detectadas.add(cls(entidad_value))
                    break
        return detectadas


@dataclass
class ResultadoPeticion:
    """Resultado de clasificacion de peticion."""
    tipo: TipoPeticion = TipoPeticion.GENERAL
    plazo_dias_habiles: int = 15
    es_urgente: bool = False
    palabra_clave_tutela: bool = False
    entidad_detectada: Optional[EntidadUrgente] = None


def clasificar_peticion(
    texto: str,
    cuerpo: str = "",
    remitente: str = "",
) -> ResultadoPeticion:
    """
    Clasifica una peticion y detecta urgencia.

    Parametros:
        texto: asunto o texto principal de la peticion
        cuerpo: cuerpo del mensaje (opcional)
        remitente: email del remitente (opcional)

    Returns ResultadoPeticion con tipo, plazo, urgencia, etc.
    """
    texto_lower = texto.lower() if texto else ""
    cuerpo_lower = cuerpo.lower() if cuerpo else ""
    remitente_lower = remitente.lower() if remitente else ""
    todo_texto = f"{texto_lower} {cuerpo_lower} {remitente_lower}"

    # --- Clasificar tipo ---
    tipo = TipoPeticion.GENERAL

    if "consulta" in texto_lower or "consulta" in cuerpo_lower:
        tipo = TipoPeticion.CONSULTA
    elif "copias" in texto_lower and "otros" in texto_lower:
        tipo = TipoPeticion.COPIAS_OTRAS
    elif "copia" in texto_lower or "copias" in texto_lower:
        tipo = TipoPeticion.COPIAS

    # --- Detectar urgencia ---
    es_urgente = False
    palabra_clave_tutela = False
    entidad_detectada: Optional[EntidadUrgente] = None

    # Tutela keyword
    if "tutela" in texto_lower or "tutela" in cuerpo_lower:
        palabra_clave_tutela = True
        es_urgente = True

    # Entidades de control
    entidades = EntidadUrgente.detectar_en_texto(todo_texto)
    if entidades:
        es_urgente = True
        # Take the first detected entity in deterministic order
        for e in EntidadUrgente:
            if e in entidades:
                entidad_detectada = e
                break

    return ResultadoPeticion(
        tipo=tipo,
        plazo_dias_habiles=tipo.plazo_dias_habiles,
        es_urgente=es_urgente,
        palabra_clave_tutela=palabra_clave_tutela,
        entidad_detectada=entidad_detectada,
    )
