from unittest.mock import patch

import fakeredis
import pytest

from balance_checker_bot.config import BCB_Settings
from balance_checker_bot.dependencies.redis_client import RedisClient

test_settings = BCB_Settings(
    CLIENT_ID="test_id",
    CLIENT_SECRET="test_password",
    SECRET_DEV="test-secret",
    REDIS_PASSWORD="password",
    REDIS_HOST="localhost",
    TELEGRAM_BOT_API_TOKEN="test",
)


# Mock get_settings function
@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr(
        "balance_checker_bot.config.get_settings", lambda: test_settings
    )
    monkeypatch.setattr(
        "balance_checker_bot.dependencies.auth_dependencies.get_settings",
        lambda: test_settings,
    )
    from balance_checker_bot.config import get_settings

    yield get_settings()  # Use yield to return the mock and allow for cleanup after tests

    # Cleanup code after yield, if necessary
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


# settings = get_settings()
# print("Mock Settings:", mock_settings)
# print("Get Settings:", settings)
# assert settings.SECRET_DEV == "test-secret", "Settings not mocked correctly"


def string_get_wrapper(original_get):
    """
    Wrapper function for fakeredis get method to return string.
    ( since the Redis mimicking library does not support decoding of bytes to strings (or just use a real dev
            Redis server next time ;) )

    :param original_get: fakeredis get method which returns bytes
    :return: decoded string
    """

    def string_get(key):
        result = original_get(key)
        if isinstance(result, bytes):
            return result.decode("utf-8")
        if isinstance(result, list):
            return [r.decode("utf-8") for r in result]
        return result

    return string_get


@pytest.fixture(autouse=True)
def mock_redis(mock_settings):
    # Setup the fake Redis server
    fake_redis = fakeredis.FakeStrictRedis()
    fake_redis.get = string_get_wrapper(fake_redis.get)
    fake_redis.set("SECRET_DEV", "test-secret")

    with patch("redis.Redis", return_value=fake_redis):
        yield fake_redis


@pytest.fixture(autouse=True)
def mock_redis_client(mock_settings, mock_redis):
    # Patch the __new__ method of RedisClient to return the fake Redis connection
    original_new = RedisClient.__new__

    def mock_new(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = original_new(cls, *args, **kwargs)
            cls._instance.connection = mock_redis
            cls._instance.get = string_get_wrapper(cls._instance.connection.get)
            cls._instance.set = cls._instance.connection.set
        return cls._instance

    with patch(
        "balance_checker_bot.dependencies.redis_client.RedisClient.__new__",
        new=mock_new,
    ):
        yield
