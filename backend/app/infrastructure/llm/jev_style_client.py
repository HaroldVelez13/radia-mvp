"""Jev-Style-0.8B-Decision-v3 fast classifier client.

Classifies documents into 7 tipos with probabilities:
factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad.
"""
import httpx


class JevStyleClient:
    """Client for Jev-Style-0.8B-Decision-v3 local classifier (0.53GB)."""

    TIPOS = [
        "factura",
        "viatico",
        "derecho_peticion",
        "oficio_control",
        "queja_transporte",
        "cotizacion",
        "publicidad",
    ]

    def __init__(self, base_url="http://jev-style:8001", model="Jev-Style-0.8B-Decision-v3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def classify(self, texto: str) -> dict:
        """
        Classify texto and return probabilities for each of the 7 tipos.

        Returns dict like:
        {"factura": 0.1, "viatico": 0.05, "derecho_peticion": 0.7, ...}
        Probabilities sum to 1.0.
        """
        try:
            resp = httpx.post(
                f"{self.base_url}/classify",
                json={"text": texto, "model": self.model},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            probs = data.get("probabilities", {})
            result = {t: float(probs.get(t, 0.0)) for t in self.TIPOS}
            total = sum(result.values())
            if total > 0:
                result = {t: round(v / total, 4) for t, v in result.items()}
            return result
        except Exception:
            # Fallback: uniform probabilities when service is unavailable
            uniform = 1.0 / len(self.TIPOS)
            return {t: round(uniform, 4) for t in self.TIPOS}
