import logging
import os
from telegram.ext import Application, CommandHandler

from db.database import init_db
from bot.handlers import (
    start_handler,
    coin_handler,
    new_handler,
    expiring_handler,
    subscribe_handler,
    unsubscribe_handler,
    mysubs_handler,
    error_handler,
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

    # Create application
    logger.info("\n[BOT] Creating Telegram bot application...")
    application = Application.builder().token(bot_token).build()

    # Register command handlers
    logger.info("[BOT] Registering command handlers...")
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("coin", coin_handler))
    application.add_handler(CommandHandler("new", new_handler))
    application.add_handler(CommandHandler("expiring", expiring_handler))
    application.add_handler(CommandHandler("subscribe", subscribe_handler))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    application.add_handler(CommandHandler("mysubs", mysubs_handler))

    # Add error handler
    application.add_error_handler(error_handler)

    logger.info("[OK] Handlers registered")

    # Start bot
    logger.info("\n[POLLING] Starting bot polling...")
    logger.info("Bot is running. Press Ctrl+C to stop.\n")

    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Keyboard interrupt received")
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
