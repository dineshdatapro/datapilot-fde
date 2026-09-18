from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env", extra="ignore")

    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = "gpt-oss:120b"
    ollama_api_key: str = ""
    max_upload_bytes: int = 10 * 1024 * 1024
    upload_dir: str = ""


settings = Settings()
