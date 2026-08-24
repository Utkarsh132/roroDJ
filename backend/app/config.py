from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    model_provider: str = "fallback"
    model_name: str = "qwen3:8b"
    ollama_url: str = "http://localhost:11434"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RORODJ_",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
