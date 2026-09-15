import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from conftest import MOCK_VALID_RESULT
from app.models.schemas import TriageResult


# ── Test 1: input válido devuelve clasificación correcta ──────────────────────
def test_valid_input_returns_classification(client):
    """El endpoint /triage responde con success=True y campos correctos."""
    mock_result = TriageResult(**MOCK_VALID_RESULT)

    with patch("app.services.triage_service.run_triage", new=AsyncMock(return_value=mock_result)):
        response = client.post(
            "/triage",
            json={
                "report_text": "Dos alumnos se pelearon en el patio y uno está llorando.",
                "provider": "ollama",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["category"] == "violencia_fisica"
    assert body["data"]["urgency_level"] == "alta"
    assert body["data"]["department"] == "direccion"
    assert body["error"] is None


# ── Test 2: alucinación estructural — el modelo devuelve texto plano ──────────
def test_hallucinated_response_does_not_crash_api(client):
    """Si el modelo devuelve texto libre en lugar de JSON, la API responde con
    success=False y un mensaje de error, sin lanzar excepción 500."""

    async def fake_triage(text, provider):
        raise ValueError("Ollama no devolvió JSON válido: Expecting value: line 1")

    with patch("app.services.triage_service.run_triage", new=AsyncMock(side_effect=fake_triage)):
        response = client.post(
            "/triage",
            json={
                "report_text": "Un alumno lleva semanas siendo ignorado por sus compañeros.",
                "provider": "ollama",
            },
        )

    assert response.status_code == 200  # la API no colapsa
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert "JSON" in body["error"]


# ── Test 3: JSON con claves faltantes — Pydantic intercepta el error ──────────
def test_missing_keys_in_llm_json_raises_validation_error(client):
    """Si el modelo omite campos obligatorios en el JSON, Pydantic lo detecta
    antes de devolver la respuesta, y la API reporta el error correctamente."""

    async def fake_triage_incomplete(text, provider):
        # simula que el modelo olvidó 'urgency_level' y 'department'
        from pydantic import ValidationError
        TriageResult(
            category="acoso",
            # urgency_level faltante
            # department faltante
            summary="Resumen incompleto",
            reasoning="Sin razonamiento",
            provider="ollama",
            model="llama3.2:3b",
            latency_ms=900.0,
        )

    with patch("app.services.triage_service.run_triage", new=AsyncMock(side_effect=fake_triage_incomplete)):
        response = client.post(
            "/triage",
            json={
                "report_text": "Una alumna está siendo acosada por sus compañeras de clase.",
                "provider": "ollama",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None


# ── Test 4: proveedor inválido devuelve error controlado ─────────────────────
def test_invalid_provider_rejected_by_schema(client):
    """El schema de Pydantic rechaza proveedores no soportados antes de
    llegar al servicio."""
    response = client.post(
        "/triage",
        json={
            "report_text": "Un alumno amenazó a un profesor en el pasillo.",
            "provider": "openai",  # no está en el patrón permitido
        },
    )

    # FastAPI devuelve 422 Unprocessable Entity por validación de schema
    assert response.status_code == 422


# ── Test 5: prompt contiene instrucciones de control de sesgos ───────────────
def test_system_prompt_contains_bias_controls():
    """El prompt del sistema incluye instrucciones explícitas anti-sesgo."""
    from app.core.prompts import SYSTEM_PROMPT

    bias_keywords = ["género", "origen", "raza", "barrio"]
    for keyword in bias_keywords:
        assert keyword in SYSTEM_PROMPT.lower(), f"Falta control de sesgo para: {keyword}"


# ── Test 6: endpoint /health responde correctamente ───────────────────────────
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
