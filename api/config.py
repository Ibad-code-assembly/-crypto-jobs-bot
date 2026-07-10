import os
from typing import List

# API Configuration
class Settings:
    # Server
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:3001",  # Next.js default
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./crypto_jobs.db"
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"


settings = Settings()
