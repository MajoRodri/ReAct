import pytest
from fastapi.testclient import TestClient
import sys
import os

# permite importar desde backend/app sin instalar el paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)


# respuesta válida que simula un modelo bien portado
MOCK_VALID_RESULT = {
    "category": "violencia_fisica",
    "urgency_level": "alta",
    "department": "direccion",
    "summary": "Pelea con golpes en el patio escolar",
    "reasoning": "Observo: agresión física. Pienso: riesgo inmediato. Clasifico: alta urgencia.",
    "provider": "ollama",
    "model": "llama3.2:3b",
    "latency_ms": 1500.0,
    "tokens_used": 98,
    "estimated_cost_usd": 0.0,
}
