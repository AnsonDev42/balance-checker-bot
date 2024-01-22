from fastapi.testclient import TestClient

from balance_checker_bot.main import app
from test import conftest

client = TestClient(app)


def test_mocked_settings(mock_settings, monkeypatch):
    monkeypatch.setattr(
        "balance_checker_bot.config.get_settings", lambda: conftest.test_settings
    )
    from balance_checker_bot.config import get_settings

    settings = get_settings()
    assert settings.SECRET_DEV == "test-secret", "Settings not mocked correctly"
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PASSWORD == "password"


def test_redis_client_contains_fake_settings(
    mock_redis, mock_settings, mock_redis_client
):
    """
    Test the Redis client contains fake settings.
    :param mock_redis:
    :param mock_settings:
    :return:
    """
    r = mock_redis_client
    secret_value = r.get("SECRET_DEV")  # Use the connection attribute

    # Test specific Redis operations here
    assert secret_value == "test-secret", r.get("SECRET_DEV")


def test_ping_authorised(mock_settings, mock_redis_client):
    # check app redis connection
    from balance_checker_bot.config import get_settings

    get_settings()
    response = client.get("/ping", headers={"secret": get_settings().SECRET_DEV})

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
