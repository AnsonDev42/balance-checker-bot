import datetime
import logging

import pydantic
import requests
from requests import HTTPError
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from balance_checker_bot.config import get_settings
from balance_checker_bot.dependencies.redis_client import RedisClient
from validator import TimeModel

settings = get_settings()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
r = RedisClient()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello! Please use /connect_monzo to authorize this bot to access your monzo account!",
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


async def get_balance_callback(context: ContextTypes):
    if context is None:
        return
    try:
        response = requests.get(
            f"{settings.BASE_URL}/balance", headers={"secret": settings.SECRET_DEV}
        )
        logging.info(str(response.json()))
        response.raise_for_status()
    except HTTPError as e:
        logging.error(e)
        await context.bot.send_message(
            chat_id=r.get("admin_user"),
            text=f"Failed to get balance! {e}",
        )
        return
    response = response.json()
    await context.bot.send_message(
        chat_id=r.get("admin_user"), text=f"Your balance is: {response}"
    )


async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't get the balance",
        )
        return
    await get_balance_callback(context)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command; " "try again!",
    )


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=chat_id,
            text="You are not the admin, you can't set the timer",
        )
        return
    try:
        if len(context.args) == 0:
            raise pydantic.ValidationError("No time provided")
        user_input_time = context.args[0]
        # show check time in the log
        logging.info(f"check_user_input_time: -{user_input_time}-")
        checked_time = TimeModel(time=user_input_time)

    except pydantic.ValidationError as e:
        err = str(e)
        await update.effective_message.reply_text(
            f"Usage: /set <DDHHMM>, your input error:{err} "
        )

    logging.info(f"reminder timer set: -{checked_time}-")
    r.rpush(r.get("admin_user"), user_input_time)

    t = datetime.time(hour=checked_time.hour, minute=checked_time.minute)
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_monthly(
        get_balance_callback,
        when=t,
        day=checked_time.day,
        chat_id=chat_id,
        name=str(chat_id),
        data=context,
    )

    text = f"Your reminder successfully set to monthly at day {checked_time.day} at {t.strftime('%H:%M')}."
    if job_removed:
        text += " Old one was removed."
    await update.effective_message.reply_text(text)


def setup_existing_reminders(job_queue):
    # Retrieve all users' chat_ids
    chat_id = r.get("admin_user")
    if chat_id is None:
        return "No admin user, no reminder set"
    reminder_times = r.lrange(chat_id, 0, -1)
    for time_str in reminder_times:
        hour = int(time_str[2:4])
        minute = int(time_str[4:6])
        t = datetime.time(hour=hour, minute=minute)

        job_queue.run_daily(
            get_balance_callback,
            time=t,
            chat_id=chat_id,
            name=f"{chat_id}_{t}",
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
        return False


async def login_monzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if the user is the admin
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )
        return
    response = requests.get(
        f"{settings.BASE_URL}/start", headers={"secret": settings.SECRET_DEV}
    )
    try:
        login_url = response.json()["auth_url"]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please login to monzo, you will be redirected to monzo login page: {login_url}",
        )
        text = "If you complete the authentication on Monzo's side, click /get_monzo_account to verify!"
    except KeyError:
        text = "failed to get auth url, please check if the server is running!"
    finally:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )
    # await get_monzo_account(update, context)


async def remove_all_jobs_from_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    reminder_times = r.lrange(chat_id, 0, -1)
    for time_str in reminder_times:
        hour = int(time_str[2:4])
        minute = int(time_str[4:6])
        t = datetime.time(hour=hour, minute=minute)

        remove_job_if_exists(f"{chat_id}_{t}", context)

    r.delete(chat_id)
    await context.bot.send_message(
        chat_id=chat_id, text="Successfully unset all reminders"
    )


async def get_monzo_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if the user is the admin
    if not is_admin(update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not the admin, you can't reset the admin",
        )
        return
    try:
        response = requests.get(
            f"{settings.BASE_URL}/accounts", headers={"secret": settings.SECRET_DEV}
        )
        logging.info(str(response.json()))
    except Exception as e:
        logging.error(e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Failed to get account ID: Error talking to the server! Check if the server and database is running!",
        )
        return

    if response.status_code == 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Got account ID from monzo! \nTrying to check your balance...",
        )
        await get_balance(update, context)
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Failed to get your balance: Please retry with /get_balance !",
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_API_TOKEN).build()
    setup_existing_reminders(application.job_queue)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect_monzo", login_monzo))
    application.add_handler(CommandHandler("get_monzo_account", get_monzo_account))
    application.add_handler(CommandHandler("reset_owner", reset_owner))
    application.add_handler(CommandHandler("get_balance", get_balance))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("unset_all", remove_all_jobs_from_db))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()
