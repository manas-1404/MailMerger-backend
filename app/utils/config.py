import os

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_CONNECTION_URL: str
    OAUTHLIB_INSECURE_TRANSPORT: int
    DEBUG: bool = False
    JWT_AUTH_ALGORITHM: str
    JWT_SIGNATURE_SECRET_KEY: str
    JWT_TOKEN_EXPIRATION_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRATION_DAYS: int
    REDIS_HOST: str
    REDIS_SERVER_PORT: int
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_PROJECT_ID: str

    class Config:
        env_file = ".env"

settings = Settings()

if settings.OAUTHLIB_INSECURE_TRANSPORT:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = str(settings.OAUTHLIB_INSECURE_TRANSPORT)