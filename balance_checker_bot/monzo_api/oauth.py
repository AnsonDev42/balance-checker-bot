import logging
import secrets
import urllib.parse
from enum import Enum, auto
from typing import Annotated

import requests
from fastapi import APIRouter, Request, Depends, HTTPException

from balance_checker_bot.config import get_settings
from balance_checker_bot.dependencies.auth_dependencies import is_auth_bot
from balance_checker_bot.dependencies.redis_client import RedisClient

oauth_router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()
r = RedisClient()


class TokenRefreshResult(Enum):
    SUCCESS = auto()
    NO_LOCAL_REFRESH_TOKEN = auto()
    NETWORK_ERROR = auto()

    def __bool__(self):
        return self == TokenRefreshResult.SUCCESS


@oauth_router.get("/start")
async def start_oauth(request: Request, is_auth: Annotated[str, Depends(is_auth_bot)]):
    """
    Redirects to Monzo OAuth2 authentication page
    :param request:
    :param token:
    :return:
    """
    auth_url, state = auth1(settings.REDIRECT_URI, settings.CLIENT_ID)
    request.session["oauth_state"] = state
    # add state to redis
    try:
        r.set("state", state)
    except Exception as e:
        logger.critical(f"failed to set state in r: {e}")
    logger.info("Authentication - redirecting to Monzo: " + auth_url)
    return {"auth_url": auth_url}


@oauth_router.get("/oauth/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if code is None:
        raise HTTPException(status_code=401, detail="code not available")
    if state is None:
        raise HTTPException(status_code=401, detail="state not available")

    if await trade_tokens(code, state):
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Error exchanging token")


async def trade_tokens(code: str, state: str) -> bool:
    """
    trade the code for an access token
    :return: True if successful, False otherwise
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URI,
        "code": code,
    }
    try:
        response = requests.post(settings.MONZO_TOKEN_URL, data=data, headers={})
        response.raise_for_status()
        tokens = str(response.json())
        logger.info("Authentication - tokens received")
        logger.debug(tokens)
        r.set("json", tokens)
        r.set("refresh_token", response.json()["refresh_token"])
        r.set("access_token", response.json()["access_token"])
        return True
    except requests.RequestException:
        logger.info("Authentication - token exchange failed")
        return False


@oauth_router.get("/refresh")
async def refresh_tokens_endpoint(request: Request):
    results = await perform_token_refresh()
    if results == TokenRefreshResult.SUCCESS:
        return {"success": True}
    elif results == TokenRefreshResult.NO_LOCAL_REFRESH_TOKEN:
        logger.debug("Refresh token not available from database")
        raise HTTPException(
            status_code=401,
            detail="Refresh token not available from database and session",
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Refresh token not available from database or Monzo rejected it",
        )


async def perform_token_refresh() -> TokenRefreshResult:
    r_token = r.get("refresh_token")
    if r_token is None:
        logger.debug("Refresh token not available from database")
        return TokenRefreshResult.NO_LOCAL_REFRESH_TOKEN

    logger.info("local refresh token retrieved.")
    # prepare data for request to monzo
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
        "refresh_token": r_token,
    }
    try:
        response = requests.post(settings.MONZO_TOKEN_URL, data=data, headers={})
        logger.info("Authentication - tokens received")
        logger.debug(str(response.json()))
        response.raise_for_status()
        if "refresh_token" in response.json() and "access_token" in response.json():
            r_token = response.json["refresh_token"]
            access_token = response.json["access_token"]
            r.set("refresh_token", r_token)
            r.set("access_token", access_token)
        logger.info("Access token and Refresh token both refreshed.")
        return TokenRefreshResult.SUCCESS
    except requests.RequestException:
        return TokenRefreshResult.NETWORK_ERROR


def auth1(redirect_url: str, client_id: str):
    if not redirect_url or redirect_url == "":
        raise ValueError("redirect_url is required")
    if not client_id or client_id == "":
        raise ValueError("client_id is required")
    state_token = secrets.token_urlsafe(128)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_url,
        "response_type": "code",
        "state": state_token,
    }
    url = "https://auth.monzo.com/?"
    user_visit_url = url + urllib.parse.urlencode(params)
    logger.info("Authentication - step 1: redirect url: " + redirect_url)
    logger.info("Authentication - step 1: send user to Monzo: " + user_visit_url)
    # http://127.0.0.1/monzo?code=somecode&state=somestate
    # the code would be used in step 2 as part of the callback url from monzo to your server
    # the state would be used to verify that the request is coming from monzo and not some other source
    return user_visit_url, state_token
