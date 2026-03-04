from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "https://*.vercel.app"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
