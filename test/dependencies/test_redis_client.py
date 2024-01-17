from balance_checker_bot.dependencies.redis_client import RedisClient


def test_redis_client_singleton(mock_redis, mock_settings):
    """
    Test the Redis client singleton.
    :param mock_redis:
    :param mock_settings:
    :return:
    """
    client1 = RedisClient()
    client2 = RedisClient()
    assert client1 is client2


def test_redis_client_functionality(mock_redis, mock_settings):
    """
    Test the Redis client functionality.
    :param mock_redis:
    :param mock_settings:
    :return:
    """
    r = RedisClient()
    # Test specific Redis operations here
    r.set("key", "value")

    assert r.get("key") == "value", r.get("key")