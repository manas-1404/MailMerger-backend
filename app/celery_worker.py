from celery import Celery

from app.utils.config import settings

celery_app = Celery(
    "fastapi_worker",
    broker = f"redis://{settings.REDIS_CLOUD_USERNAME}:{settings.REDIS_CLOUD_PASSWORD}@{settings.REDIS_CLOUD_HOST}:{settings.REDIS_CLOUD_PORT}/0",
    backend = f"redis://{settings.REDIS_CLOUD_USERNAME}:{settings.REDIS_CLOUD_PASSWORD}@{settings.REDIS_CLOUD_HOST}:{settings.REDIS_CLOUD_PORT}/0"
    # broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_SERVER_PORT}/{settings.REDIS_SERVER_DB}",
    # backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_SERVER_PORT}/{settings.REDIS_SERVER_DB}",
)

celery_app.autodiscover_tasks(['app.tasks'])