import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "TruthLens"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Universal Google API Key (can be used for Gemini, Fact Check, and Google Search)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Specific API Keys (fall back to GOOGLE_API_KEY if not explicitly set)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    GOOGLE_FACTCHECK_API_KEY: str = os.getenv("GOOGLE_FACTCHECK_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", os.getenv("GOOGLE_CSE_ID", ""))
    
    # Third-Party News API Keys
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # Gemini Client-Side Rate Limiter Configuration
    GEMINI_MAX_RPM: int = 15  # Free tier safe limit (below 20 RPM)
    GEMINI_MAX_RETRIES: int = 2
    GEMINI_INITIAL_BACKOFF_SEC: float = 1.5
    GEMINI_MIN_INTER_CALL_DELAY_SEC: float = 0.5
    
    # Database & Cache settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/truthlens.db")
    CACHE_TTL_HOURS: int = 72
    FUZZY_MATCH_THRESHOLD: float = 85.0
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "chrome-extension://*",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
