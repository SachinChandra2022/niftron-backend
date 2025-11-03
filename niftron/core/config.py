# src/niftron/core/config.py

import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    """Reads configuration from environment variables."""
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    # Provide a default value for settings that might not be in the .env file
    MARKET_SUFFIX: str = os.getenv("MARKET_SUFFIX", ".NS")

settings = Settings()


if not settings.DATABASE_URL:
    raise ValueError("FATAL_ERROR: DATABASE_URL environment variable is not set or accessible.")