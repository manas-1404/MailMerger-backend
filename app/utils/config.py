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

    class Config:
        env_file = ".env"

settings = Settings()

if settings.OAUTHLIB_INSECURE_TRANSPORT:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = str(settings.OAUTHLIB_INSECURE_TRANSPORT)