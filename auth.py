import redis

from dotenv import dotenv_values

from monzo.authentication import Authentication


def auth1(redirect_url, client_id, client_secret):
    monzo = Authentication(
        client_id=client_id, client_secret=client_secret, redirect_url=redirect_url
    )
    state_token = monzo.state_token
    print("step 1")
    print(state_token)
    # The user should visit this url
    user_visit_url = monzo.authentication_url

    print(user_visit_url)
    # http://127.0.0.1/monzo?code=somecode&state=somestate
    # the code would be used in step 2 as part of the callback url from monzo to your server
    # the state would be used to verify that the request is coming from monzo and not some other source

    return (
        user_visit_url,  #
        state_token,
    )


def test_auth1():
    client_id = config.get("CLIENT_ID")
    client_secret = config.get("CLIENT_SECRET")
    redirect_uri = config.get(
        "REDIRECT_URI"
    )  # URL requests via Monzo will be redirected in a browser

    auth1(redirect_uri, client_id, client_secret)


if __name__ == "__main__":
    # auth1()
    config = dotenv_values(".env")

    test_auth1()
    psw = config.get("REDIS_PASSWORD")
    r = redis.Redis(host="localhost", port=6379, decode_responses=True, password=psw)
    r.set("foo", "bar1")
    print(r.get("foo"))
