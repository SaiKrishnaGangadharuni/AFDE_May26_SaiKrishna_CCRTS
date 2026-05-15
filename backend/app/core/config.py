"""Application configuration loaded from environment with sane defaults."""
from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../backend


class Settings(BaseSettings):
    PROJECT_NAME: str = "Customer Complaint & Resolution Tracking System"
    PROJECT_CODE: str = "CCRTS"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # SQLite database file lives inside backend/ so the repo stays self-contained.
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'ccrts.db'}"

    # JWT
    SECRET_KEY: str = "change-me-in-prod-please-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # CORS — Vite dev server runs on 5173 by default
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Uploads
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
