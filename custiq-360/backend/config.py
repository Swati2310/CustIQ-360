from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load .env from the project root (one level above backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
# Also try loading from the backend directory itself
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


class Settings(BaseSettings):
    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBED_MODEL: str = "gemini-embedding-001"

    # Storage
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    DATABASE_URL: str = "sqlite:///./data/custiq.db"

    # API
    CORS_ORIGINS: str = "http://localhost:5173"

    # Scheduler
    ALERT_CHECK_INTERVAL: int = 86400  # seconds — 24 h

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        # Accept comma-separated list stored as a single string;
        # the property below exposes it as a list.
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
