from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_CONNECTION_URL: str
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
