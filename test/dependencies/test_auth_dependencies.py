import pytest

from balance_checker_bot.dependencies.auth_dependencies import is_auth_bot


@pytest.mark.asyncio
async def test_is_auth_bot(mock_redis, mock_settings):
    """
    Test is_auth_bot function.
    :return:
    """
    test_secret = "test-secret"
    # Test correct secret
    verified = await is_auth_bot(test_secret)  # Use await for async function
    assert verified is True
