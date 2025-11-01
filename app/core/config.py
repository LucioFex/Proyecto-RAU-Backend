from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "RAU"
    ENV: str = "dev"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
