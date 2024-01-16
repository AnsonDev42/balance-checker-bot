import redis
from balance_checker_bot.config import get_settings


# singleton pattern for redis connection
_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=6379,  # Or make this configurable as well
            decode_responses=True,
            password=settings.REDIS_PASSWORD,
        )
    return _redis_client
