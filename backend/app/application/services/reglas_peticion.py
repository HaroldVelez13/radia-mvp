from app.domain.enums import Dependencia, EstadoRadicado

def clasificar_peticion(texto: str) -> str:
    # Detecta tipo peticion para plazo
    texto_lower = texto.lower()
    if "copia" in texto_lower and "concepto" not in texto_lower and "consulta" not in texto_lower:
        # Solo copias?
        if len(texto_lower.split()) < 50:  # heuristica simple
            return "copias"
    if "concepto" in texto_lower or "consulta" in texto_lower:
        return "consulta"
    return "general"

def es_peticion_implicita(texto: str) -> bool:
    keywords = ["solicito", "les pido que me informen", "derecho de peticion", "peticion"]
    return any(k in texto.lower() for k in keywords)
