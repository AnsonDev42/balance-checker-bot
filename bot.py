import datetime
import logging
import pydantic
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import dotenv_values
from query_balance import get_balance
from validator import TimeModel

config = dotenv_values(".env")
API_TOKEN = config.get("API_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please use /getmonzotoken to set monzo token",
    )


#
async def getBalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_balance())


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


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


if __name__ == "__main__":
    application = ApplicationBuilder().token(API_TOKEN).build()

    start_handler = CommandHandler("start", start)
    # goodbye_handler = CommandHandler('goodbye', goodbye)
    get_balance_handler = CommandHandler("getbalance", getBalance)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(start_handler)
    application.add_handler(get_balance_handler)
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(echo_handler)
    application.add_handler(unknown_handler)

    application.run_polling()
