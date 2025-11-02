from __future__ import annotations
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    app_name: str = "RAU"
    env: str = "dev"
    api_v1_prefix: str = "/api/v1"

    # Auth
    secret_key: str = "change-this-in-prod"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # DB (nuevos)
    database_url: str | None = None
    database_url_direct: str | None = None
    storage_backend: str = "memory"   # "pg" para usar Postgres

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",            # usamos nombres tal cual en .env
        case_sensitive=False,
        extra="ignore",           # <<< evita el error por claves "extra"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v):
        # admite "http://localhost:5173,https://midominio.com"
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

settings = Settings()
