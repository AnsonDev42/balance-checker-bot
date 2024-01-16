import redis
from balance_checker_bot.config import get_settings


class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not RedisClient._instance:
            cls._instance = super(RedisClient, cls).__new__(cls, *args, **kwargs)
            settings = get_settings()
            cls._instance.connection = redis.Redis(
                host=settings.REDIS_HOST,
                port=6379,  # Or make this configurable as well
                decode_responses=True,
                password=settings.REDIS_PASSWORD,
            )
        return cls._instance.connection
