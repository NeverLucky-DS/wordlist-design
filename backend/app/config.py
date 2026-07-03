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
    grok_api_key: str = ""
    grok_model: str = "grok-4"  # grok-3 retired (HTTP 410)
    default_user_id: int = 1

    # Pipeline tuning
    pipeline_target_words: int = 60     # control loop: keep going until this many words/topic
    pipeline_min_phrases: int = 12      # minimum Redemittel per topic
    pipeline_batch_size: int = 6        # words per Mistral enrichment call
    pipeline_max_supplement_rounds: int = 3

    # Autonomous mode (topic queue scheduler)
    pipeline_autorun: bool = True
    pipeline_interval_minutes: int = 30
    pipeline_max_attempts: int = 3
    pipeline_stale_run_minutes: int = 120  # watchdog: running longer → failed

    # Auto-topics: keep the queue filled without manual input
    pipeline_auto_topics: bool = True
    pipeline_auto_topics_batch: int = 3
    cors_origins: str = "http://127.0.0.1:8753,http://localhost:8753,http://127.0.0.1:5173"


settings = Settings()
