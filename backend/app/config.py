from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"
    secure_cookies: bool = False
    admin_emails: str = ""
    cors_origins: str = "http://127.0.0.1:8753,http://localhost:8753,http://127.0.0.1:5173"


settings = Settings()
