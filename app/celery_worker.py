from celery import Celery

from app.utils.config import settings

UPSTASH_REDIS_CONNECTION_URL: str = settings.REDIS_CLOUD_URL + "?ssl_cert_reqs=none"

celery_app = Celery(
    "fastapi_worker",
    broker = UPSTASH_REDIS_CONNECTION_URL,
    backend = UPSTASH_REDIS_CONNECTION_URL
)

#for async support
celery_app.conf.update(
    broker_use_ssl={"ssl_cert_reqs": "CERT_NONE"},
    redis_backend_use_ssl={"ssl_cert_reqs": "CERT_NONE"},
    worker_pool="custom",
    worker_pool_cls="celery_aio_pool.pool:AsyncIOPool"
)

celery_app.autodiscover_tasks(['app.tasks.celery_tasks'])