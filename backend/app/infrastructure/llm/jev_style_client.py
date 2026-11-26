"""Jev-Style-0.8B-Decision-v3 fast classifier client.

Classifies documents into 7 tipos with probabilities:
factura, viatico, derecho_peticion, oficio_control, queja_transporte, cotizacion, publicidad.

First tries http://jev-style:8001, if not available loads model locally
via transformers from HF cache.
"""

import logging
from typing import Dict

import httpx
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

TIPOS = [
    "factura",
    "viatico",
    "derecho_peticion",
    "oficio_control",
    "queja_transporte",
    "cotizacion",
    "publicidad",
]


class JevStyleClient:
    """Client for Jev-Style-0.8B-Decision-v3 local classifier (0.53GB).

    Tries remote service at http://jev-style:8001 first. If unavailable,
    falls back to loading the model locally from Hugging Face cache.
    """

    def __init__(self, base_url: str = "http://jev-style:8001", model: str = "Jev-Style-0.8B-Decision-v3"):
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self._model = None
        self._tokenizer = None
        self._device = "cpu"

    def _try_remote(self, texto: str) -> dict | None:
        """Try classification via remote jev-style service."""
        try:
            resp = httpx.post(
                f"{self.base_url}/classify",
                json={"text": texto, "model": self.model_name},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            probs = data.get("probabilities", {})
            result = {t: float(probs.get(t, 0.0)) for t in TIPOS}
            total = sum(result.values())
            if total > 0:
                result = {t: round(v / total, 4) for t, v in result.items()}
            return result
        except Exception as e:
            logger.warning(f"Remote jev-style service unavailable: {e}")
            return None

    def _load_local_model(self):
        """Load model and tokenizer from HF cache."""
        if self._model is not None:
            return
        try:
            logger.info(f"Loading local model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load local model {self.model_name}: {e}")
            self._model = None
            self._tokenizer = None

    def _classify_local(self, texto: str) -> dict:
        """Classify using local model."""
        if self._model is None or self._tokenizer is None:
            self._load_local_model()
            if self._model is None:
                # Ultimate fallback: uniform probabilities
                uniform = 1.0 / len(TIPOS)
                return {t: round(uniform, 4) for t in TIPOS}

        try:
            inputs = self._tokenizer(texto, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
                # Assuming model outputs 7 probabilities matching TIPOS order
                result = {t: float(p) for t, p in zip(TIPOS, probs)}
                total = sum(result.values())
                if total > 0:
                    result = {t: round(v / total, 4) for t, v in result.items()}
                return result
        except Exception as e:
            logger.error(f"Local classification error: {e}")
            uniform = 1.0 / len(TIPOS)
            return {t: round(uniform, 4) for t in TIPOS}

    def classify(self, texto: str) -> dict:
        """
        Classify texto and return probabilities for each of the 7 tipos.

        Returns dict like:
        {"factura": 0.1, "viatico": 0.05, "derecho_peticion": 0.7, ...}
        Probabilities sum to 1.0.

        Tries remote service first, falls back to local model, then uniform.
        """
        # Try remote first
        result = self._try_remote(texto)
        if result is not None:
            return result

        # Fallback to local model
        return self._classify_local(texto)