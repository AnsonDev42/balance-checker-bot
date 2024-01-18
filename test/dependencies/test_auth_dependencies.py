import pytest


@pytest.mark.asyncio
async def test_is_auth_bot(mock_settings, mock_redis, mock_redis_client):
    """
    Test is_auth_bot function.
    :return:
    """
    # need to import get_settings here to use the mocked settings, otherwise it will use the real settings
    from balance_checker_bot.config import get_settings

    # Test correct secret
    from balance_checker_bot.dependencies.auth_dependencies import is_auth_bot

    verified = await is_auth_bot(
        get_settings().SECRET_DEV
    )  # Use await for async function
    assert verified is True, "is_auth_bot failed "
