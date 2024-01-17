from unittest.mock import patch

import fakeredis
import pytest

from balance_checker_bot.config import Settings


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
    with patch("redis.Redis", return_value=fake_redis):
        yield fake_redis
