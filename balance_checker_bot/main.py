import logging
import os
from pathlib import Path
from typing import Annotated
import uvicorn
from fastapi import FastAPI, Depends
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from balance_checker_bot.monzo_api.oauth import oauth_router as monzo_oauth_router
from balance_checker_bot.monzo_api.operations import (
    operations_router as monzo_operations_router,
)
from balance_checker_bot.dependencies.auth_dependencies import is_auth_bot
from balance_checker_bot.dependencies.redis_client import RedisClient
from balance_checker_bot.config import get_settings


settings = get_settings()


app = FastAPI()
app.include_router(monzo_oauth_router)
app.include_router(monzo_operations_router)

# Session Middleware
app.add_middleware(SessionMiddleware, secret_key=os.urandom(50))
app.add_middleware(HTTPSRedirectMiddleware)

logger = logging.getLogger(__name__)

scopes = ["accounts"]  # Adjust the scopes according to your needs
r = RedisClient()


@app.get("/ping")
async def ping(
    is_authenticated: Annotated[str, Depends(is_auth_bot)], refresh: bool | None = False
):
    authorised = True if is_authenticated else False
    return {"ping": "pong", "authorised": authorised, "refreshed": refresh}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=f"{str(Path(__file__).parent)}/log_conf.yaml",
        reload=True,
        ssl_certfile="./ssl/cert.pem",
        ssl_keyfile="./ssl/key.pem",
        proxy_headers=True,
    )
