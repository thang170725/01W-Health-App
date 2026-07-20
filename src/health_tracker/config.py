"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise RuntimeError("Missing DB_URL in the project .env file.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
