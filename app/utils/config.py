import os
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_CONNECTION_URL: str
    NEON_DB_CONNECTION_URL: str
    SUPABASE_ACCESS_KEY_ID: str
    SUPABASE_SERVICE_ROLE: str
    ALLOWED_ORIGINS: list[str] = []
    OAUTHLIB_INSECURE_TRANSPORT: int
    DEBUG: bool = False
    JWT_AUTH_ALGORITHM: str
    JWT_SIGNATURE_SECRET_KEY: str
    JWT_TOKEN_EXPIRATION_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRATION_DAYS: int
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_PROJECT_ID: str

    REDIS_CLOUD_URL: str

    REDIS_CLOUD_HOST: str
    REDIS_CLOUD_PORT: int
    REDIS_CLOUD_USERNAME: str
    REDIS_CLOUD_PASSWORD: str

    RATE_LIMIT_PER_SECOND: int
    RATE_LIMIT_CAPACITY: int
    RATE_LIMIT_IDLE_TTL: int
    RATE_DEFAULT_COST: int
    RATE_HEAVY_COST: int
    RATE_HEAVY_PATHS: str = ""
    RATE_SKIP_PATHS: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

if settings.OAUTHLIB_INSECURE_TRANSPORT:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = str(settings.OAUTHLIB_INSECURE_TRANSPORT)