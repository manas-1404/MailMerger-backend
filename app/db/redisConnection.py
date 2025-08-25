from redis.asyncio import Redis
from app.utils.config import settings

redis_client: Redis = Redis.from_url(settings.REDIS_CLOUD_URL, decode_responses=True)

async def get_redis_connection() -> Redis:
    """
    Dependency to get a Redis connection.
    This function can be used in FastAPI routes to get a Redis connection for caching.
    """
    return redis_client

# def get_redis_connection():
#     """
#     Dependency to get a Redis connection.
#     This function can be used in FastAPI routes to get a Redis connection for caching.
#     """
#     redis_client = redis.Redis(
#         host=settings.REDIS_CLOUD_HOST,
#         port=settings.REDIS_CLOUD_PORT,
#         decode_responses=True,
#         username=settings.REDIS_CLOUD_USERNAME,
#         password=settings.REDIS_CLOUD_PASSWORD,
#     )
#
#     # redis_client = redis.Redis(
#     #     host=settings.REDIS_HOST,
#     #     port=settings.REDIS_SERVER_PORT,
#     #     db=0,
#     #     decode_responses=True
#     # )
#
#     try:
#         yield redis_client
#     finally:
#         pass