class RedisClient:
    _instance = None

    @staticmethod
    def set_mock_connection(mock_redis):
        RedisClient._instance.connection = mock_redis
        return RedisClient
