"""Carga y valida la configuración desde el archivo .env."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

REQUIRED_VARS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_OWNER_ID",
    "GOOGLE_CREDENTIALS_FILE",
    "GOOGLE_SHEET_ID",
)


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_owner_id: int
    google_credentials_file: str
    google_sheet_id: str
    ai_provider: str
    timezone: str


def load_settings(env_file: str = ".env") -> Settings:
    load_dotenv(env_file)

    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        raise ValueError(f"Faltan variables en .env: {', '.join(missing)}")

    return Settings(
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_owner_id=int(os.environ["TELEGRAM_OWNER_ID"]),
        google_credentials_file=os.environ["GOOGLE_CREDENTIALS_FILE"],
        google_sheet_id=os.environ["GOOGLE_SHEET_ID"],
        ai_provider=os.getenv("AI_PROVIDER", "gemini"),
        timezone=os.getenv("TIMEZONE", "America/Bogota"),
    )
