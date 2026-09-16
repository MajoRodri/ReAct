"""Cliente para el modelo local Ollama (llama3.x) via API REST."""

import json
import time
import httpx
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.schemas import TriageResult


class OllamaClient:
    """Encapsula las llamadas HTTP al servidor Ollama local."""

    def __init__(self):
        """Lee la URL base y el modelo desde la configuración de entorno."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def triage(self, report_text: str, history: list = None) -> TriageResult:
        """Envía el reporte al modelo y devuelve el resultado de triaje.

        Construye el prompt completo (system + user), hace POST a /api/chat,
        mide la latencia y delega el parseo a _parse_response.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(report_text, history)},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # baja temperatura = respuestas más deterministas
                "top_p": 0.9,
            },
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

        latency_ms = (time.monotonic() - start) * 1000
        body = response.json()

        raw_content = body["message"]["content"]
        tokens_used = body.get("eval_count")

        return self._parse_response(raw_content, latency_ms, tokens_used)

    def _parse_response(self, raw: str, latency_ms: float, tokens_used) -> TriageResult:
        """Convierte el JSON crudo del modelo en un TriageResult validado por Pydantic.

        Lanza ValueError si el modelo devuelve texto no parseable como JSON;
        Pydantic rechaza cualquier campo fuera del schema (alucinaciones de claves).
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ollama no devolvió JSON válido: {e}")

        return TriageResult(
            category=data["category"],
            urgency_level=data["urgency_level"],
            department=data["department"],
            summary=data["summary"],
            reasoning=data["reasoning"],
            provider="ollama",
            model=self.model,
            latency_ms=round(latency_ms, 2),
            tokens_used=tokens_used,
            estimated_cost_usd=0.0,  # local = sin coste
        )
