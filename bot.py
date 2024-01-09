import datetime
import logging
import pydantic
import redis
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from query_balance import get_balance
from validator import TimeModel
from config import Settings
from functools import lru_cache
import requests


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=6379,
    decode_responses=True,
    password=settings.REDIS_PASSWORD,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please use /getmonzotoken to set monzo token",
    )
    if (admin := r.get("admin_user")) is None:
        r.set("admin_user", update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are the first user, you are the admin",
        )
    elif admin == update.effective_chat.id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are the admin",
        )


#
async def getBalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_balance())


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command; " "try again!",
    )


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job
    balance = get_balance()
    if balance == "Error":
        await context.bot.send_message(
            job.chat_id, text="Error, can't get balance, please check your monzo token!"
        )
        return
    text = f" Balance: {balance} pounds"
    if balance < 100:
        text = "Your balance is less than 100 pounds, please top up! " + text
    else:
        text = (
            "Your balance is more than 100 pounds, keep above it for direct debit! "
            + text
        )
    await context.bot.send_message(job.chat_id, text=text)


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        user_input_time = context.args[0]
        # show check time in the log
        logging.info(f"check_user_input_time: -{user_input_time}-")
        checked_time = TimeModel(time=user_input_time)
        logging.info(f"reminder timer set: -{checked_time}-")
        t = datetime.time(hour=checked_time.hour, minute=checked_time.minute)
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_daily(
            alarm,
            time=t,
            chat_id=chat_id,
            name=str(chat_id),
        )

        text = f"Your reminder successfully set to everyday {t.strftime('%H:%M')}."
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except pydantic.ValidationError as e:
        err = str(e)
        await update.effective_message.reply_text(
            f"Usage: /set <DDHHMM>, your input error:{err} "
        )


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = (
        "Timer successfully cancelled!" if job_removed else "You have no active timer."
    )
    await update.message.reply_text(text)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def reset_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curr_user = str(update.effective_chat.id)
    if (admin_id := r.get("admin_user")) is None:
        r.set("admin_user", curr_user)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Reset succeed, you are the admin now!",
        )
    elif admin_id == curr_user:
        r.delete("admin_user")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You were the admin, now you are not",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )


def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curr_user = str(update.effective_chat.id)
    if curr_user == r.get("admin_user"):
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )
        return False


async def login_monzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if the user is the admin
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )
        return
    response = requests.get(f"{settings.BASE_URL}/?secret={settings.SECRET_DEV}")
    try:
        login_url = response.json()["auth_url"]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please login to monzo, you will be redirected to monzo login page: {login_url}",
        )
        return
    except KeyError:
        text = "failed to get auth url, please check if the server is running!"
    finally:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )


async def get_monzo_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if the user is the admin
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )
        return
    u = f"{settings.BASE_URL}/accounts?secret={settings.SECRET_DEV}"
    logging.info(u)
    try:
        response = requests.get(u)
        logging.info(str(response.json()))
    except Exception as e:
        logging.error(e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Error talking to the server! Check if the server and database is running!",
        )
        return

    if response.status_code == 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Got account id from monzo! Now checking your balance!",
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Error in the server! Check server's error!",
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(settings.API_TOKEN).build()

    start_handler = CommandHandler("start", start)
    login_handler = CommandHandler("login", login_monzo)
    get_balance_handler = CommandHandler("getbalance", getBalance)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(start_handler)
    application.add_handler(login_handler)
    application.add_handler(CommandHandler("reset", reset_owner))
    application.add_handler(CommandHandler("getbalance", getBalance))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(unknown_handler)

    application.run_polling()
