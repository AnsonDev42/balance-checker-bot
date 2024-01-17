from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BCB_Settings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str = "https://localhost:1234/auth/callback"
    REDIS_PASSWORD: str = (
        "password"  # change in docker-compose.yml as well if you use docker
    )
    REDIS_HOST: str = "localhost"
    SECRET_DEV: str = "replace-me-with-a-secret"
    SSL_CERTFILE: str = "ssl/cert.pem"
    SSL_KEYFILE: str = "ssl/key.pem"
    TELEGRAM_BOT_API_TOKEN: str = "test"
    BASE_URL: str = "https://localhost:1234"  # Change this to your server's URL

    @field_validator("BASE_URL")
    def ensure_trailing_slash(cls, v):
        if v.endswith("/"):
            raise ValueError("BASE_URL should not end in a slash")
        return v

    # Static configurations can be directly set as class attributes
    MONZO_TOKEN_URL: str = "https://api.monzo.com/oauth2/token"
    WHOAMI_URL: str = "https://api.monzo.com/ping/whoami"
    ACCOUNTS_URL: str = "https://api.monzo.com/accounts"
    BALANCE_URL: str = "https://api.monzo.com/balance"

    model_config = SettingsConfigDict()


@lru_cache
def get_settings():
    return BCB_Settings(
        _env_file=Path(__file__).parent.parent / ".env",
        _env_file_encoding="utf-8",
    )
