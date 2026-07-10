import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from telegram.request import HTTPXRequest
import httpx
from dotenv import load_dotenv

load_dotenv()

from db.database import init_db
from bot.handlers import (
    start_handler,
    coin_handler,
    new_handler,
    upcoming_handler,
    expiring_handler,
    jobs_handler,
    newcoins_handler,
    subscribe_handler,
    unsubscribe_handler,
    mysubs_handler,
    error_handler,
    message_handler,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the bot."""
    # Get token from environment
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN not found in .env file")
        return

    logger.info("="*70)
    logger.info("CRYPTO JOBS BOT - TELEGRAM")
    logger.info("="*70)

    # Initialize database
    logger.info("\n[INIT] Initializing database...")
    init_db()
    logger.info("[OK] Database initialized")

    # Create application with optional proxy support
    logger.info("\n[BOT] Creating Telegram bot application...")

    proxy_url = os.getenv("TELEGRAM_PROXY")
    if proxy_url:
        logger.info(f"[PROXY] Using proxy: {proxy_url}")
        try:
            client = httpx.AsyncClient(proxy=proxy_url, timeout=30.0)
            request = HTTPXRequest(client=client)
            application = Application.builder().token(bot_token).request(request).build()
            logger.info("[OK] Application created with proxy")
        except Exception as e:
            logger.error(f"[PROXY ERROR] Failed to configure proxy: {e}")
            application = Application.builder().token(bot_token).build()
    else:
        application = Application.builder().token(bot_token).build()

    # Register command handlers
    logger.info("[BOT] Registering command handlers...")
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("coin", coin_handler))
    application.add_handler(CommandHandler("new", new_handler))
    application.add_handler(CommandHandler("upcoming", upcoming_handler))
    application.add_handler(CommandHandler("expiring", expiring_handler))
    application.add_handler(CommandHandler("jobs", jobs_handler))
    application.add_handler(CommandHandler("newcoins", newcoins_handler))
    application.add_handler(CommandHandler("subscribe", subscribe_handler))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    application.add_handler(CommandHandler("mysubs", mysubs_handler))

    # Register message handler for keywords
    logger.info("[BOT] Registering message handler for keyword detection...")
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Add error handler
    application.add_error_handler(error_handler)

    logger.info("[OK] Handlers registered")

    # Start bot
    logger.info("\n[POLLING] Starting bot polling...")
    logger.info("Bot is running. Press Ctrl+C to stop.\n")

    try:
        # allowed_updates=None means receive all updates
        application.run_polling(allowed_updates=None)
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Keyboard interrupt received")
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
