from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from balance_checker_bot.main import app
from balance_checker_bot.monzo_api.oauth import TokenRefreshResult

client = TestClient(app)


def test_start_oauth_no_token():
    response = client.get("/start")

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}


def test_start_oauth_with_token(mock_settings, mock_redis_client):
    from balance_checker_bot.config import get_settings

    response = client.get(
        "/start",
        headers={"secret": get_settings().SECRET_DEV},
    )

    assert response.status_code == 200


@pytest.fixture
def mock_trade_tokens_success():
    with patch("balance_checker_bot.monzo_api.oauth.trade_tokens") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_trade_tokens_failure():
    with patch("balance_checker_bot.monzo_api.oauth.trade_tokens") as mock:
        mock.return_value = False
        yield mock


@pytest.mark.asyncio
async def test_callback_success(mock_trade_tokens_success):
    response = client.get("/oauth/callback?code=somecode&state=somestate")
    assert response.status_code == 200
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_callback_failure(mock_trade_tokens_failure):
    response = client.get("/oauth/callback?code=somecode&state=somestate")
    assert response.status_code == 400
    assert response.json() == {"detail": "Error exchanging token"}


@pytest.fixture
def mock_perform_token_refresh_success():
    with patch("balance_checker_bot.monzo_api.oauth.perform_token_refresh") as mock:
        mock.return_value = TokenRefreshResult.SUCCESS
        yield mock


@pytest.fixture
def mock_perform_token_refresh_no_local_refresh_token():
    with patch("balance_checker_bot.monzo_api.oauth.perform_token_refresh") as mock:
        mock.return_value = TokenRefreshResult.NO_LOCAL_REFRESH_TOKEN
        yield mock


@pytest.mark.asyncio
async def test_refresh_tokens_success(mock_perform_token_refresh_success):
    response = client.get("/refresh")
    assert response.status_code == 200
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_refresh_tokens_no_local_refresh_token(
    mock_perform_token_refresh_no_local_refresh_token,
):
    response = client.get("/refresh")
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Refresh token not available from database and session"
    }
