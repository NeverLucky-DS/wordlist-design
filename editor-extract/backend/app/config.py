from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://deutsch:deutsch@127.0.0.1:5432/deutsch_trainer"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"
    default_user_id: int = 1
    cors_origins: str = "http://127.0.0.1:5173"


settings = Settings()
