import httpx

class OllamaClient:
    def __init__(self, base_url="http://ollama:11434", model="qwen3:8b"):
        self.base_url = base_url
        self.model = model

    def chat_json(self, prompt: str) -> dict:
        # T3.1: implementar llamada con JSON mode
        # POST /api/chat {model, messages, format: "json"}
        return {"tipo": "factura", "confianza": 0.9}
