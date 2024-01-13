# Balance Checker Bot
A Telegram bot for monitoring Monzo bank balances and ensuring timely direct debit payments.
## Motivation
I have a friend living in the UK who uses Monzo as his primary bank account. He often forgets to top up his balance account and misses direct debit payments. This bot was created to help him keep track of his balance and avoid late payment fees and bad credit score. It's also a great opportunity to learn about the Monzo API and Telegram bot development.

## Introduction
Balance Checker is a simple yet powerful tool designed to help you keep track of your Monzo bank account balance. It uses a Telegram bot to provide real-time balance updates and reminds you of upcoming direct debits. This ensures you never miss a payment due to an insufficient balance. The project is open-source and contributions are warmly welcomed.

Contributor: [AnsonDev42](https://github.com/AnsonDev42) \
Reviewer and Prospective Contributor: [hanwe98](https://github.com/hanwe98)

## Instructions

### Setting Up Your Environment Variables
For the bot to function properly, you need to set several environment variables. Rename `.env.example` to `.env` and fill in the bold fields. You'll need:

- OAuth **Client_ID** and **Client_SECRET** from [Monzo Bank](https://developers.monzo.com/).
- Your domain name (**BASE_URL** and **REDIRECT_URI**), and set up **REDIRECT_URI** on the Monzo developer portal for redirection.
- SSL certificate and key (stored in `balance_checker/ssl`).
- A reverse proxy server (like nginx or Cloudflare Tunnel) to redirect traffic from your local FastAPI server to your domain.
- A Redis database (**REDIS_HOST** and **REDIS_PASSWORD**) — skip if using docker-compose.
- **TELEGRAM_BOT_API_TOKEN** from [Telegram](https://core.telegram.org/bots/api).
- A [URL-friendly](https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe) **SECRET_DEV** token for secure server-bot communication.

### Running the Server and Bot

#### Using Docker Compose (Recommended)
1. Install Docker and Docker Compose.
2. Edit `docker/.env-docker` with your API keys.
3. Execute `docker compose up -d` in the project's root directory.

#### Running on Host Machine
1. Install Python 3.12, pipx, and dependencies.
2. Access `YOUR_DOMAIN_NAME/ping` to verify server functionality.

## Using the Telegram Bot
1. `/start` to initiate the bot and designate yourself as the admin.
2. `/connect_to_monzo` to link your Monzo account.
3. `/get_balance` to receive your current balance.

## Contributions
### Environment Setup with Poetry
1. Install Poetry: `pipx install poetry`.
2. Install dependencies: `poetry install`.
3. Activate the virtual environment: `poetry shell`.

### Setting Up Pre-Commit Hooks
We utilize pre-commit for code quality checks.
1. Install pre-commit: `pipx install pre-commit`.
2. Install hooks: `pre-commit install`.
3. Optionally, run `pre-commit run --all-files`.

## Legal Disclaimer
This project is not affiliated with Monzo Bank or Telegram. It's an independent tool designed for convenience. Users are responsible for secure handling of their data and the consequences of using this bot. The developer assumes no liability for any financial losses or breaches of privacy arising from the use of Balance Checker.
