import requests
from dotenv import dotenv_values

config = dotenv_values(".env")
USER_ID = config.get("USER_ID")
ACCESS_TOKEN = config.get("ACCESS_TOKEN")
ACCOUNT_ID = config.get("ACCOUNT_ID")


def get_balance():
    try:
        header = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        }
        r = requests.get(
            f"https://api.monzo.com/balance?account_id={ACCOUNT_ID}", headers=header
        )
        print(r.json())
        balance = r.json()["balance"] / 100  # convert to pounds from pence
        return balance
    except Exception as e:
        print(e)
        return "Error"


if __name__ == "__main__":
    get_balance()
