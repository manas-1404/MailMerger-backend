from celery import Celery

from app.utils.config import settings

celery_app = Celery(
    "fastapi_worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_SERVER_PORT}/{settings.REDIS_SERVER_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_SERVER_PORT}/{settings.REDIS_SERVER_DB}",
)