"""Ollama LLM client with JSON mode and model fallback."""
import json
import httpx


class OllamaClient:
    """Client for Ollama local LLM (qwen3.5:4b primary, qwen3:8b fallback)."""

    def __init__(self, base_url="http://ollama:11434", model="qwen3.5:4b", fallback_model="qwen3:8b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback_model = fallback_model

    def chat_json(self, prompt: str) -> dict:
        """
        Send a prompt to Ollama with JSON mode and return parsed dict.

        Tries primary model (qwen3.5:4b), falls back to qwen3:8b on failure.
        Returns dict with at least: tipo, confianza, motivo.
        """
        last_error = None
        for model in (self.model, self.fallback_model):
            try:
                resp = httpx.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "format": "json",
                        "stream": False,
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "{}")
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    parsed = {"tipo": "desconocido", "confianza": 0.0, "motivo": "Invalid JSON response"}
                return parsed
            except Exception as exc:  # httpx.RequestError, json.JSONDecodeError, etc.
                last_error = exc
                continue

        # All models failed: return safe fallback
        return {
            "tipo": "desconocido",
            "confianza": 0.0,
            "motivo": f"Ollama unavailable: {last_error}",
        }
