import asyncio
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from telegram.error import TimedOut, TelegramError
import httpx
from db.database import init_db, SessionLocal
from scraper.scheduler import JobScheduler
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
    unknown_command_handler,
)
from bot.notifications import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_logs.txt", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class IntegratedBot:
    """Combined bot and scheduler system."""

    def __init__(self):
        """Initialize bot and scheduler."""
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN not found in .env")

        self.scheduler = None
        self.app = None
        self.notification_manager = None

    def start(self):
        """Start bot and scheduler."""
        logger.info("="*70)
        logger.info("CRYPTO JOBS BOT - INTEGRATED (Bot + Scheduler + Notifications)")
        logger.info("="*70)
        logger.info(f"Bot token: {self.bot_token[:20]}...***")

        # Initialize database
        logger.info("\n[INIT] Initializing database...")
        init_db()
        logger.info("[OK] Database initialized")

        # Create Telegram application with longer timeouts and optional proxy support
        logger.info("\n[BOT] Creating Telegram application...")
        logger.info("[BOT] Using extended timeouts (60 seconds) for Telegram API...")

        # Check for proxy configuration
        proxy_url = os.getenv("TELEGRAM_PROXY")
        try:
            if proxy_url:
                logger.info(f"[PROXY] Using proxy: {proxy_url}")
                request = HTTPXRequest(
                    proxy=proxy_url,
                    connect_timeout=60.0,
                    read_timeout=60.0,
                    write_timeout=60.0,
                    pool_timeout=60.0,
                )
            else:
                # Create HTTPXRequest with longer timeout (no proxy)
                request = HTTPXRequest(
                    connect_timeout=60.0,
                    read_timeout=60.0,
                    write_timeout=60.0,
                    pool_timeout=60.0,
                )

            self.app = Application.builder().token(self.bot_token).request(request).build()
            logger.info("[OK] Application created with 60-second timeout")
        except Exception as e:
            logger.error(f"[ERROR] Failed to create application with custom timeout: {e}")
            logger.info("[FALLBACK] Attempting to create application with default settings...")
            try:
                self.app = Application.builder().token(self.bot_token).build()
                logger.info("[OK] Application created with default settings")
            except Exception as e2:
                logger.error(f"[CRITICAL] Failed to create application: {e2}")
                raise

        # Register command handlers
        logger.info("[BOT] Registering command handlers...")
        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("coin", coin_handler))
        self.app.add_handler(CommandHandler("new", new_handler))
        self.app.add_handler(CommandHandler("upcoming", upcoming_handler))
        self.app.add_handler(CommandHandler("expiring", expiring_handler))
        self.app.add_handler(CommandHandler("jobs", jobs_handler))
        self.app.add_handler(CommandHandler("newcoins", newcoins_handler))
        self.app.add_handler(CommandHandler("subscribe", subscribe_handler))
        self.app.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
        self.app.add_handler(CommandHandler("mysubs", mysubs_handler))

        # Register message handler for plain-text keywords
        logger.info("[BOT] Registering message handler for keyword detection...")
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

        # Unknown commands like /BTC /ETH /XMR → treated as coin lookups (must be LAST)
        self.app.add_handler(MessageHandler(filters.COMMAND, unknown_command_handler))

        self.app.add_error_handler(error_handler)

        logger.info("[OK] Command handlers registered")

        # Create notification manager
        logger.info("\n[NOTIFY] Creating notification manager...")
        db = SessionLocal()
        self.notification_manager = NotificationManager(self.app, db)
        logger.info("[OK] Notification manager created")

        # Create scheduler
        logger.info("\n[SCHEDULER] Creating job scheduler...")
        self.scheduler = JobScheduler()
        logger.info("[OK] Scheduler created")

        # Start scheduler in background thread (runs every 4 hours)
        logger.info("\n[SCHEDULER] Starting scheduler in background thread (every 4 hours)...")
        import threading
        scheduler_thread = threading.Thread(
            target=lambda: asyncio.run(self._start_scheduler_with_notifications()),
            daemon=True
        )
        scheduler_thread.start()
        logger.info("[OK] Scheduler thread started")

        # Start bot with retry logic
        logger.info("\n[POLLING] Starting bot with retry logic...")
        logger.info("Bot is running. Press Ctrl+C to stop.\n")
        self._run_bot_with_retries()

    def _run_bot_with_retries(self):
        """Run bot polling with exponential backoff retry logic."""
        max_retries = 3  # Reduced to 3 since network is genuinely blocked
        retry_count = 0
        base_wait = 5  # Start with 5 seconds

        while True:
            try:
                # Use synchronous polling (not await)
                self.app.run_polling(allowed_updates=None)
                # If we get here, polling ended normally
                logger.info("\n[SHUTDOWN] Bot polling ended normally")
                break

            except (KeyboardInterrupt, SystemExit):
                logger.info("\n[SHUTDOWN] Keyboard interrupt received")
                break

            except (TimedOut, TimeoutError, TelegramError, Exception) as e:
                retry_count += 1
                wait_time = base_wait * (2 ** (retry_count - 1))  # Exponential backoff: 5, 10, 20 seconds

                logger.error(f"\n[NETWORK ERROR] Attempt {retry_count}/{max_retries} failed: {type(e).__name__}")
                logger.error(f"Details: {str(e)[:200]}")
                logger.error("\nPossible causes:")
                logger.error("  • ISP/Network blocking Telegram API (port 443)")
                logger.error("  • Firewall still blocking despite rules added")
                logger.error("  • Corporate proxy intercepting HTTPS")
                logger.error("  • Telegram API temporarily unavailable")

                if retry_count >= max_retries:
                    logger.error(f"\n[FALLBACK] Max retries ({max_retries}) reached.")
                    logger.warning("========================================")
                    logger.warning("Switching to SCRAPER-ONLY MODE")
                    logger.warning("========================================")
                    logger.warning("✓ Job scraping is still ACTIVE")
                    logger.warning("✓ Jobs stored in database every 6 hours")
                    logger.warning("✗ Telegram messages DISABLED")
                    logger.warning("\nTo fix: Try a VPN or contact your network admin")
                    logger.warning("========================================\n")
                    # Keep the scheduler running even if Telegram is unavailable
                    self._run_fallback_mode()
                    break
                else:
                    logger.warning(f"\n[RETRY] Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                    logger.warning("Solutions to try:")
                    logger.warning("  1. Restart your computer (firewall rules need restart)")
                    logger.warning("  2. Try a VPN (ProtonVPN, ExpressVPN)")
                    logger.warning("  3. Check TELEGRAM_PROXY in .env file\n")
                    time.sleep(wait_time)

    def _run_fallback_mode(self):
        """Run in scraper-only mode without Telegram connectivity."""
        logger.info("\n" + "="*70)
        logger.info("FALLBACK MODE: Scraper Only (No Telegram Messages)")
        logger.info("="*70)
        logger.info("✓ Job scraping is ACTIVE - running every 6 hours")
        logger.info("✓ Jobs are being STORED in the database")
        logger.info("✗ Telegram notifications are DISABLED")
        logger.info("="*70 + "\n")

        # Keep the scheduler running even if Telegram is unavailable
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN] Keyboard interrupt received")

    async def _start_scheduler_with_notifications(self):
        """Start scheduler with integrated notifications."""
        async def scheduled_job_with_notifications():
            """Run scrapers then send group notifications for jobs and new coins."""
            logger.info("\n[SCHEDULED] Running periodic scrape...")
            result = await self.scheduler.run_all_scrapers()

            db = SessionLocal()

            # JOBS NOTIFICATIONS
            if result.get("new", 0) > 0:
                logger.info(f"[SCHEDULED] {result['new']} new jobs — sending group notifications...")
                from db.models import Job

                new_jobs = db.query(Job).filter(
                    Job.created_at >= result["timestamp"],
                    Job.is_active == True,
                ).all()

                if new_jobs and self.notification_manager:
                    notify_result = await self.notification_manager.notify_all_new_jobs(new_jobs)
                    logger.info(
                        f"[SCHEDULED] Job notifications: {notify_result['total_sent']} sent, "
                        f"{notify_result['total_failed']} failed"
                    )

            # COINS NOTIFICATIONS
            if result.get("new_coins", 0) > 0:
                logger.info(f"[SCHEDULED] {result['new_coins']} new coins — sending alert...")
                from db.models import NewCoinListing

                new_coins = db.query(NewCoinListing).filter(
                    NewCoinListing.created_at >= result["timestamp"],
                    NewCoinListing.is_active == True,
                ).order_by(NewCoinListing.listed_date.desc()).all()

                if new_coins and self.notification_manager:
                    # Group by symbol for display
                    coins_dict = {}
                    for coin in new_coins[:30]:
                        if coin.coin_symbol not in coins_dict:
                            coins_dict[coin.coin_symbol] = []
                        coins_dict[coin.coin_symbol].append({
                            "exchange": coin.exchange,
                            "listed_date": coin.listed_date,
                            "trading_pairs": coin.trading_pairs,
                        })
                    await self.notification_manager.send_new_coins_alert(coins_dict)

            db.close()

        # START SCHEDULER IMMEDIATELY (don't wait for initial scrape)
        try:
            self.scheduler.scheduler.remove_job("scrape_all_sites")
        except Exception:
            pass

        self.scheduler.scheduler.add_job(
            scheduled_job_with_notifications,
            "interval",
            hours=4,
            id="scrape_all_sites_with_notifications",
            name="Scrape all sites and send notifications",
            misfire_grace_time=300,
        )

        # Start scheduler NOW - don't block the bot!
        self.scheduler.scheduler.start()
        logger.info("[OK] Scheduler started - ready to receive bot messages!")

        # NOW run the initial scrape in the background (won't block bot)
        logger.info("\n[STARTUP] Running initial scrape in background...")
        result = await self.scheduler.run_all_scrapers()

        db = SessionLocal()

        # Handle notifications if we got new jobs
        if result.get("new", 0) > 0:
            logger.info(f"[STARTUP] {result['new']} new jobs found, sending notifications...")
            from db.models import Job
            new_jobs = db.query(Job).filter(Job.created_at >= result["timestamp"]).all()

            if new_jobs and self.notification_manager:
                notify_result = await self.notification_manager.notify_all_new_jobs(new_jobs)
                logger.info(f"[STARTUP] Job notifications: {notify_result['total_sent']} sent, "
                           f"{notify_result['total_failed']} failed")

        # Handle notifications if we got new coins
        if result.get("new_coins", 0) > 0:
            logger.info(f"[STARTUP] {result['new_coins']} new coins found, sending alert...")
            from db.models import NewCoinListing
            new_coins = db.query(NewCoinListing).filter(
                NewCoinListing.created_at >= result["timestamp"]
            ).order_by(NewCoinListing.listed_date.desc()).all()

            if new_coins and self.notification_manager:
                # Group by symbol for display
                coins_dict = {}
                for coin in new_coins[:30]:
                    if coin.coin_symbol not in coins_dict:
                        coins_dict[coin.coin_symbol] = []
                    coins_dict[coin.coin_symbol].append({
                        "exchange": coin.exchange,
                        "listed_date": coin.listed_date,
                        "trading_pairs": coin.trading_pairs,
                    })
                await self.notification_manager.send_new_coins_alert(coins_dict)

        db.close()

        logger.info(f"[STARTUP] Initial scrape complete: {result['new']} jobs, {result['new_coins']} coins")

    async def stop(self):
        """Stop bot and scheduler gracefully."""
        logger.info("\n[SHUTDOWN] Stopping scheduler...")
        if self.scheduler:
            await self.scheduler.stop()

        logger.info("[SHUTDOWN] Stopping bot...")
        if self.app:
            await self.app.stop()

        logger.info("[OK] All services stopped")


def main():
    """Main entry point."""
    try:
        bot = IntegratedBot()
        bot.start()  # Synchronous call
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
