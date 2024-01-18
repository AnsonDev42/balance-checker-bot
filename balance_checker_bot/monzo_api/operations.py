from fastapi import APIRouter, Request, Depends, HTTPException
import requests
import logging
from typing import Annotated
from balance_checker_bot.dependencies.auth_dependencies import is_auth_bot
from balance_checker_bot.dependencies.redis_client import RedisClient
from balance_checker_bot.config import get_settings
from balance_checker_bot.monzo_api.oauth import oauth_router, perform_token_refresh

logger = logging.getLogger(__name__)
settings = get_settings()
r = RedisClient()
operations_router = APIRouter()

operations_router.include_router(oauth_router)


@operations_router.get("/whoami")
async def whoami(request: Request, token: Annotated[str, Depends(is_auth_bot)]):
    if not await perform_token_refresh():
        raise HTTPException(status_code=401, detail="Failed to refresh token")
    access_token = load_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(settings.WHOAMI_URL, data={}, headers=headers)
        logger.info("Authentication - tokens received")
        response.raise_for_status()
        logger.debug(f"whoami response: {response.json()}")
        if (
            "authenticated" in response.json()
            and str(response.json()["authenticated"]) == "True"
        ):
            logger.info("Authentication - user authenticated by Monzo")

            return "You are authenticated"
        else:
            raise HTTPException(
                status_code=401, detail="You are not authenticated by Monzo!"
            )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, detail="Something wrong with the request for whoami"
        ) from e


def load_access_token():
    access_token = r.get("access_token")
    if access_token:
        logger.debug(f"access token:{str(access_token)}")
        return access_token
    raise HTTPException(status_code=401, detail="No access token found")


@operations_router.get("/accounts")
async def get_accounts(request: Request, token: Annotated[str, Depends(is_auth_bot)]):
    if not await perform_token_refresh():
        raise HTTPException(status_code=401, detail="Failed to refresh token")

    access_token = load_access_token()
    data = {}
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.debug(f"account request headers: {headers}")
    try:
        response = requests.get(settings.ACCOUNTS_URL, data=data, headers=headers)
        logger.info("Authentication - tokens received")
        response.raise_for_status()
        logger.debug(f"accounts response: {response.json()}")
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, detail="Something wrong with the request for accounts"
        ) from e
    res = response.json()
    logger.debug(f"raw account json: {res}")
    account_list = []
    for account_item in res["accounts"]:
        account = {
            "account_id": account_item["id"],
            "description": account_item["description"],
            "created": account_item["created"],
            "closed": account_item["closed"],
        }
        account_list.append(account)

    logger.debug(f"account list: {account_list}")
    account_id = account_list[0]["account_id"]
    logger.debug(f"account id: {account_id}")
    r.set("account_id", account_id)
    return "account id is saved"


@operations_router.get("/balance")
async def get_balance(request: Request, is_auth: Annotated[str, Depends(is_auth_bot)]):
    if not await perform_token_refresh():
        raise HTTPException(status_code=401, detail="Failed to refresh token")
    account_id = r.get("account_id")
    logger.debug(f"balance: account id: {account_id}")
    access_token = load_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"account_id": account_id}
    try:
        response = requests.get(
            settings.BALANCE_URL,
            params=params,
            headers=headers,
        )
        logger.info("Balance request - got response")
        response.raise_for_status()
        logger.debug(f"accounts response: {response.json()}")
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, detail="Something wrong with the request for accounts"
        ) from e

    balance = response.json()["balance"]
    balance = balance / 100
    logger.debug(f"balance: {balance}")
    return balance
