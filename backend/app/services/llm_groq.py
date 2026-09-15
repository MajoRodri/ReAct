import json
import time
import asyncio
from pathlib import Path
from dotenv import dotenv_values
from groq import Groq, RateLimitError, APIStatusError
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT, build_user_prompt
from app.models.schemas import TriageResult

MAX_RETRIES = 3
BASE_BACKOFF = 2.0  # segundos

# Read model directly from .env file to avoid system env-var overrides
_ENV_PATH = Path(__file__).parents[3] / ".env"
_ENV_VALS = dotenv_values(_ENV_PATH)


class GroqClient:

    def __init__(self):
        api_key = _ENV_VALS.get("GROQ_API_KEY") or settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY no configurada en .env")
        self.client = Groq(api_key=api_key)
        self.model = _ENV_VALS.get("GROQ_MODEL") or settings.groq_model
        print(f"[GroqClient] usando modelo: {self.model!r}", flush=True)

    async def triage(self, report_text: str, history: list = None) -> TriageResult:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(report_text, history)},
        ]

        for attempt in range(MAX_RETRIES):
            try:
                start = time.monotonic()
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                latency_ms = (time.monotonic() - start) * 1000
                return self._parse_response(completion, latency_ms)

            except RateLimitError:
                if attempt == MAX_RETRIES - 1:
                    raise
                # backoff exponencial
                wait = BASE_BACKOFF ** (attempt + 1)
                await asyncio.sleep(wait)

            except APIStatusError as e:
                raise ValueError(f"Error de API Groq: {e.status_code} - {e.message}")

    def _parse_response(self, completion, latency_ms: float) -> TriageResult:
        raw = completion.choices[0].message.content
        usage = completion.usage

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Groq no devolvió JSON válido: {e}")

        tokens = usage.total_tokens if usage else None
        cost = (tokens / 1_000_000 * settings.groq_cost_per_million_tokens) if tokens else None

        return TriageResult(
            category=data["category"],
            urgency_level=data["urgency_level"],
            department=data["department"],
            summary=data["summary"],
            reasoning=data["reasoning"],
            provider="groq",
            model=self.model,
            latency_ms=round(latency_ms, 2),
            tokens_used=tokens,
            estimated_cost_usd=round(cost, 6) if cost else None,
        )
