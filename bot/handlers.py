import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from db.database import SessionLocal
from db.queries import (
    get_jobs_by_coin,
    find_new_jobs,
    find_expiring_jobs,
    add_subscription,
    remove_subscription,
    get_user_subscriptions,
)
from bot.formatters import (
    format_start_message,
    format_job_card,
    format_jobs_list,
    format_new_jobs,
    format_expiring_jobs,
    format_subscriptions,
)

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    try:
        message = format_start_message()
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in start_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def coin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /coin command to show jobs for a specific coin."""
    try:
        if not context.args:
            await update.message.reply_text(
                "Please specify a coin ticker.\n\nExample: <code>/coin BTC</code>",
                parse_mode=ParseMode.HTML
            )
            return

        coin = context.args[0].upper()
        db = SessionLocal()

        try:
            jobs = get_jobs_by_coin(coin, db)

            if not jobs:
                await update.message.reply_text(
                    f"🪙 <b>{coin}</b>\n\nNo active jobs found.",
                    parse_mode=ParseMode.HTML
                )
                return

            title = f"🪙 <b>{coin}</b> — {len(jobs)} active jobs"
            message = format_jobs_list(jobs, title)

            await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

            # Send detailed cards for first 3 jobs
            for i, job in enumerate(jobs[:3]):
                card = format_job_card(job)
                await update.message.reply_text(card, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

                if i < 2:
                    await update.message.reply_text("—", parse_mode=ParseMode.HTML)

            if len(jobs) > 3:
                await update.message.reply_text(
                    f"<i>...and {len(jobs) - 3} more jobs. Use /new or /expiring to see more.</i>",
                    parse_mode=ParseMode.HTML
                )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in coin_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new command to show jobs from last 24 hours."""
    try:
        db = SessionLocal()

        try:
            jobs = find_new_jobs(hours=24, db=db)

            if not jobs:
                await update.message.reply_text(
                    "✨ <b>New Jobs (Last 24h)</b>\n\nNo new jobs found.",
                    parse_mode=ParseMode.HTML
                )
                return

            message = format_new_jobs(jobs)
            await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in new_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def expiring_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expiring command to show jobs with deadlines in next 48 hours."""
    try:
        db = SessionLocal()

        try:
            jobs = find_expiring_jobs(hours=48, db=db)

            if not jobs:
                await update.message.reply_text(
                    "⏰ <b>Jobs Expiring Soon</b>\n\nNo jobs expiring in the next 48 hours.",
                    parse_mode=ParseMode.HTML
                )
                return

            message = format_expiring_jobs(jobs)
            await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in expiring_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe command."""
    try:
        if not context.args:
            await update.message.reply_text(
                "Please specify a coin ticker.\n\nExample: <code>/subscribe ETH</code>",
                parse_mode=ParseMode.HTML
            )
            return

        coin = context.args[0].upper()
        user_id = update.effective_user.id
        db = SessionLocal()

        try:
            success = add_subscription(user_id, coin, db)

            if success:
                await update.message.reply_text(
                    f"✅ <b>Subscribed to {coin}</b>\n\nYou'll get notifications for new {coin} jobs!",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"ℹ️ You're already subscribed to {coin}.",
                    parse_mode=ParseMode.HTML
                )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in subscribe_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unsubscribe command."""
    try:
        if not context.args:
            await update.message.reply_text(
                "Please specify a coin ticker.\n\nExample: <code>/unsubscribe ETH</code>",
                parse_mode=ParseMode.HTML
            )
            return

        coin = context.args[0].upper()
        user_id = update.effective_user.id
        db = SessionLocal()

        try:
            success = remove_subscription(user_id, coin, db)

            if success:
                await update.message.reply_text(
                    f"✅ <b>Unsubscribed from {coin}</b>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"ℹ️ You're not subscribed to {coin}.",
                    parse_mode=ParseMode.HTML
                )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in unsubscribe_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def mysubs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mysubs command to show user's subscriptions."""
    try:
        user_id = update.effective_user.id
        db = SessionLocal()

        try:
            subs = get_user_subscriptions(user_id, db)
            message = format_subscriptions(subs)
            await update.message.reply_text(message, parse_mode=ParseMode.HTML)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in mysubs_handler: {str(e)}")
        await update.message.reply_text("Sorry, an error occurred. Please try again.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")
    if update and update.message:
        try:
            await update.message.reply_text(
                "Sorry, an error occurred. Please try again or use /start for help."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
