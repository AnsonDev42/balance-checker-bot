from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    REDIS_PASSWORD: str
    REDIS_HOST: str
    SECRET_DEV: str = "secret-dev-please-change-in-env-file"
    SSL_CERTFILE: str = "ssl/cert.pem"
    SSL_KEYFILE: str = "ssl/key.pem"
    TELEGRAM_BOT_API_TOKEN: str
    BASE_URL: str

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

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env")


@lru_cache
def get_settings():
    return Settings()
