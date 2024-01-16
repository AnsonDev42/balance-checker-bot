import redis
from fastapi.testclient import TestClient

from balance_checker_bot.main import app
from balance_checker_bot.config import get_settings
from balance_checker_bot.dependencies.redis_client import RedisClient

settings = get_settings()
client = TestClient(app)


def test_redis_up():
    r = RedisClient()
    assert isinstance(r, redis.Redis)

    try:
        r.ping()
    except Exception as e:
        print(e)
        assert False, "Failed to connect to redis"


def test_ping_authorised():
    # check app redis connection
    token = "secret-dev-please-change-in-env-file"
    response = client.get("/ping", headers={"secret": token})

    assert response.status_code == 200, response.text
    assert response.json()["ping"] == "pong"
    assert response.json()["authorised"] is True


def test_ping_no_or_wrong_authorised():
    response = client.get(
        "/ping",
    )
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Not authenticated"}
    token = "some random token"
    response = client.get(
        "/ping",
        headers={"token": token},
    )
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_ping_wrong_header():
    correct_dev_token = "secret-dev-please-change-in-env-file"
    response = client.get("/ping", headers={"token": correct_dev_token})
    assert response.status_code == 403, response.text
