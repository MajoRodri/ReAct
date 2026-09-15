from pathlib import Path
from pydantic_settings import BaseSettings

# config.py está en backend/app/core/ → la raíz del proyecto está 3 niveles arriba
_ENV_FILE = str(Path(__file__).parents[3] / ".env")


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_cost_per_million_tokens: float = 0.59
    gmail_user: str = ""
    gmail_app_password: str = ""

    class Config:
        env_file = _ENV_FILE
        extra = "ignore"


settings = Settings()
