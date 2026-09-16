"""Servicio de triaje: selecciona el proveedor LLM y ejecuta el análisis."""

from app.models.schemas import TriageResult


async def run_triage(report_text: str, provider: str, history: list = None) -> TriageResult:
    """Instancia el cliente LLM correcto según `provider` y devuelve el TriageResult.

    Importación diferida para evitar cargar ambos clientes en cada request;
    solo se importa el que corresponde al proveedor solicitado.
    Lanza ValueError si el proveedor no es 'ollama' ni 'groq'.
    """
    if provider == "ollama":
        from app.services.llm_ollama import OllamaClient
        client = OllamaClient()
    elif provider == "groq":
        from app.services.llm_groq import GroqClient
        client = GroqClient()
    else:
        raise ValueError(f"Proveedor no soportado: {provider}")

    return await client.triage(report_text, history)
