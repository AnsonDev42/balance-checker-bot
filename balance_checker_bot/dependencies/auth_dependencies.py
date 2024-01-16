from fastapi import Header, HTTPException, status
from balance_checker_bot.config import Settings
import secrets


async def is_auth_bot(secret: str = Header(None)) -> bool:
    """
    Check if the request is sent by your bot and if the secret is correct
    :param secret: secret key in the dotenv file
    :return: True if the request is sent by your bot or raise error if not
    """
    # check env variable settings
    settings = Settings()
    if not secret or secret == "":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # prevent timing attacks
    if not secrets.compare_digest(
        settings.SECRET_DEV.encode("utf-8"), secret.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
