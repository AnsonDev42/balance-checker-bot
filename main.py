import os

import redis
import requests
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi import HTTPException
from dotenv import dotenv_values
import logging

logger = logging.getLogger(__name__)
config = dotenv_values(".env")
USER_ID = config.get("USER_ID")
ACCESS_TOKEN = config.get("ACCESS_TOKEN")
ACCOUNT_ID = config.get("ACCOUNT_ID")
client_id = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
app = FastAPI()
MONZO_TOKEN_URL = "https://api.monzo.com/oauth2/token"
# Session Middleware
app.add_middleware(SessionMiddleware, secret_key=os.urandom(50))
app.add_middleware(HTTPSRedirectMiddleware)

redirect_uri = config.get("REDIRECT_URI")
auth_url = "https://auth.monzo.com/"
scopes = ["accounts"]  # Adjust the scopes according to your needs
psw = config.get("REDIS_PASSWORD")
r = redis.Redis(host="localhost", port=6379, decode_responses=True, password=psw)


#
@app.get("/refresh")
async def refresh_token(request: Request):
    refresh_token = None
    if "refresh_token" in request.session:
        logger.info("Refresh token available from session")
        refresh_token = request.session["refresh_token"]
    if not refresh_token:
        logger.info("Refresh token not available from session")
        logger.debug("Try retrieve refresh token from database")
        refresh_token = r.get("refresh_token")
        if refresh_token is None:
            logger.debug("Refresh token not available from database")
            raise HTTPException(
                status_code=401,
                detail="Refresh token not available from database and session",
            )
    logger.info("refresh token retrieved.")

    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(MONZO_TOKEN_URL, data=data, headers={})
        tokens = response.json()

        logger.info("Authentication - tokens received")
        logger.debug(str(tokens))
        response.raise_for_status()
        r.set("json", str(tokens))
        r.set("access_token", tokens["access_token"])
        if "refresh_token" in response.json():
            refresh_token = tokens["refresh_token"]
            r.set("refresh_token", refresh_token)
        else:
            logger.info("Refresh token not available in response")
        if "access_token" in response.json():
            access_token = tokens["access_token"]
            r.set("access_token", access_token)
        else:
            logger.info("Access token not available in response")
        logger.info("Access token and Refresh token both refreshed.")
        request.session["oauth_token"] = tokens["access_token"]
        return RedirectResponse(url="/ping?refreshed=true")
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, detail="Could not refresh the access token"
        ) from e


@app.get("/")
async def demo(request: Request):
    from auth import auth1

    auth_url, state = auth1(redirect_uri, client_id, CLIENT_SECRET)

    request.session["oauth_state"] = state
    # add state to redis
    try:
        await r.set("state", state)
    except Exception as e:
        print(e)
    print("step 1: redirect to monzo: ", auth_url)
    return RedirectResponse(auth_url)


@app.get("/oauth/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if code is None:
        raise HTTPException(status_code=401, detail="code not available")
    if state is None:
        raise HTTPException(status_code=401, detail="state not available")

    # save code and state to redis
    print("code: ", code)
    print("state: ", state)
    try:
        r.set("code", code)
        r.set("state", state)
    except Exception as e:
        print(e)
    logger.info("Authorization successful. Access token stored.")
    return RedirectResponse("/trade")


@app.get("/trade")
async def trade(request: Request):
    # get code and state from redis
    logger.info("Authentication - swapping authorization token for an access token")
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": config.get("REDIRECT_URI"),
        "code": r.get("code"),
    }
    try:
        response = requests.post(MONZO_TOKEN_URL, data=data, headers={})
        response.raise_for_status()
        tokens = str(response.json())
        logger.info("Authentication - tokens received")
        logger.debug(tokens)
        r.set("json", tokens)
        r.set("refresh_token", response.json()["refresh_token"])
        r.set("access_token", response.json()["access_token"])
        return RedirectResponse(app.url_path_for("ping"))
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail="Error exchanging token") from e


@app.get("/ping")
async def ping(request: Request):
    print(r.get("state"))
    print(r.get("code"))
    print(r.get("refresh_token"))
    refresh_status = request.query_params.get("refresh")
    if refresh_status == "true":
        return "Access token refreshed."
    return "nothing pong"


@app.get("/whoami")
async def whoami(request: Request):
    secret = request.query_params.get("secret")
    if secret != config.get("SECRET_DEV"):
        raise HTTPException(status_code=401, detail="You are a bad guy!")
    access_token = r.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token found")
    logger.debug("access token: ", access_token)
    WHOAMI_URL = "https://api.monzo.com/ping/whoami"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(WHOAMI_URL, data={}, headers=headers)
        logger.info("Authentication - tokens received")
        response.raise_for_status()
        logger.debug("whoami response: ", response.json())
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

    #
    # @app.get("/balance")
    # async def get_balance(request: Request):
    #     user_id = None
    #     if "USER_ID" in config:
    #         user_id = config.get("USER_ID")
    #     if user_id is None:
    #         user_id = r.get("USER_ID")
    #     if user_id is None:
    #         raise HTTPException(status_code=401, detail="no user id provided")
    #     access_token = r.get("access_token")
    #
    #     if not access_token:
    #         raise HTTPException(status_code=401, detail="No access token found")
    #     BALANCE_URL = "https://api.monzo.com/balance"
    #      = {"account_id": ACCOUNT_ID}
    # if "oauth_token" not in request.session:
    #     raise HTTPException(status_code=401, detail="Not authenticated")
    #
    # # access_token = request.session["oauth_token"]["access_token"]
    # http "https://api.monzo.com/accounts" \
    #      "Authorization: Bearer $access_token"
    # accounts_response = requests.get(
    #     "https://api.monzo.com/accounts",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # ).json()
    # #
    # account_id = accounts_response["accounts"][0]["id"]
    # balance_response = requests.get(
    #     "https://api.monzo.com/balance",
    #     headers={"Authorization": f"Bearer {access_token}"},
    #     params={"account_id": account_id},
    # ).json()
    balance = 100
    return balance


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config="log_conf.yaml",
        # reload=True,
        ssl_certfile=config.get("SSL_CERTFILE"),
        ssl_keyfile=config.get("SSL_KEYFILE"),
        proxy_headers=True,
    )
