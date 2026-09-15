from app.models.schemas import TriageResult


async def run_triage(report_text: str, provider: str, history: list = None) -> TriageResult:
    if provider == "ollama":
        from app.services.llm_ollama import OllamaClient
        client = OllamaClient()
    elif provider == "groq":
        from app.services.llm_groq import GroqClient
        client = GroqClient()
    else:
        raise ValueError(f"Proveedor no soportado: {provider}")

    return await client.triage(report_text, history)
