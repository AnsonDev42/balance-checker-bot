from fastapi.testclient import TestClient
from balance_checker_bot.main import app

client = TestClient(app)


def test_start_oauth_no_token():
    response = client.get("/start")

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}
