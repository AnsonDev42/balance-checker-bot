from unittest.mock import patch

import fakeredis
import pytest

from balance_checker_bot.config import Settings
from balance_checker_bot.dependencies.redis_client import RedisClient


# Mock get_settings function
@pytest.fixture
def mock_settings():
    test_settings = Settings(
        REDIS_HOST="localhost",
        REDIS_PASSWORD="password",
        SECRET_DEV="test-secret",
    )

    with patch("balance_checker_bot.config.get_settings", return_value=test_settings):
        yield test_settings


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
        return result.decode("utf-8") if result is not None else result

    return string_get


@pytest.fixture
def mock_redis():
    # Setup the fake Redis server
    fake_redis = fakeredis.FakeStrictRedis()
    fake_redis.get = string_get_wrapper(fake_redis.get)
    fake_redis.set("SECRET-DEV", "test-secret")
    with patch("redis.Redis", return_value=fake_redis):
        yield fake_redis


@pytest.fixture
def mock_redis_client(mock_redis):
    # Patch the __new__ method of RedisClient to return the fake Redis connection
    original_new = RedisClient.__new__

    def mock_new(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = original_new(cls, *args, **kwargs)
            cls._instance.connection = mock_redis
        return cls._instance

    with patch(
        "balance_checker_bot.dependencies.redis_client.RedisClient.__new__",
        new=mock_new,
    ):
        yield


def test_redis_client_contains_fake_settings(
    mock_redis,
):
    """
    Test the Redis client contains fake settings.
    :param mock_redis:
    :param mock_settings:
    :return:
    """
    r = RedisClient()
    secret_value = r.get("SECRET_DEV")  # Use the connection attribute

    # Test specific Redis operations here
    assert secret_value == "test-secret", r.get("SECRET_DEV")
