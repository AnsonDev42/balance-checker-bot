from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USER_ID: str
    ACCESS_TOKEN: str
    ACCOUNT_ID: str
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    REDIS_PASSWORD: str
    REDIS_HOST: str
    SECRET_DEV: str
    SSL_CERTFILE: str
    SSL_KEYFILE: str
    API_TOKEN: str

    # Static configurations can be directly set as class attributes
    MONZO_TOKEN_URL: str = "https://api.monzo.com/oauth2/token"
    WHOAMI_URL: str = "https://api.monzo.com/ping/whoami"
    ACCOUNTS_URL: str = "https://api.monzo.com/accounts"
    BALANCE_URL: str = "https://api.monzo.com/balance"

    model_config = SettingsConfigDict(env_file=".env")
