#!/usr/bin/env python3
"""Minimal bot test - replies to 'hi' with 'hi'"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("ERROR: BOT_TOKEN not found in .env file!")
    exit(1)

logger.info(f"Bot token loaded: {BOT_TOKEN[:20]}...***")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all messages - reply to 'hi' with 'hi'"""
    if not update.message or not update.message.text:
        return

    user = update.effective_user.username or update.effective_user.first_name
    text = update.message.text

    logger.info(f"[MESSAGE] {user}: {text}")

    # Reply to "hi"
    if "hi" in text.lower():
        logger.info(f"[REPLY] Sending 'hi' to {user}")
        await update.message.reply_text("hi")
    else:
        logger.info(f"[SKIP] No 'hi' in message")


async def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("MINIMAL BOT TEST")
    logger.info("="*60)

    # Create application
    logger.info("\n[BOT] Creating application...")
    app = Application.builder().token(BOT_TOKEN).build()
    logger.info("[OK] Application created")

    # Add message handler
    logger.info("[BOT] Registering message handler...")
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    logger.info("[OK] Message handler registered")

    # Start polling
    logger.info("\n[POLLING] Starting polling...")
    logger.info("Bot is running. Send 'hi' in Telegram group.\n")

    try:
        await app.run_polling(allowed_updates=None)
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Bot stopped by user")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
