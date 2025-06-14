from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_CONNECTION_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
