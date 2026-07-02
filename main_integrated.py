import asyncio
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from telegram.error import TimedOut
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

        # Create Telegram application with optional proxy support
        logger.info("\n[BOT] Creating Telegram application...")

        # Check for proxy configuration
        proxy_url = os.getenv("TELEGRAM_PROXY")
        if proxy_url:
            logger.info(f"[PROXY] Using proxy: {proxy_url}")
            try:
                # Create custom HTTP client with proxy
                client = httpx.AsyncClient(
                    proxy=proxy_url,
                    timeout=30.0
                )
                request = HTTPXRequest(client=client)
                self.app = Application.builder().token(self.bot_token).request(request).build()
                logger.info("[OK] Application created with proxy")
            except Exception as e:
                logger.error(f"[PROXY ERROR] Failed to configure proxy: {e}")
                logger.info("[FALLBACK] Creating application without proxy")
                self.app = Application.builder().token(self.bot_token).build()
        else:
            self.app = Application.builder().token(self.bot_token).build()
            logger.info("[OK] Application created (no proxy configured)")

        # Register command handlers
        logger.info("[BOT] Registering command handlers...")
        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("coin", coin_handler))
        self.app.add_handler(CommandHandler("new", new_handler))
        self.app.add_handler(CommandHandler("upcoming", upcoming_handler))
        self.app.add_handler(CommandHandler("expiring", expiring_handler))
        self.app.add_handler(CommandHandler("jobs", jobs_handler))
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

        # Start scheduler in background thread (runs every 6 hours)
        logger.info("\n[SCHEDULER] Starting scheduler in background thread (every 6 hours)...")
        import threading
        scheduler_thread = threading.Thread(
            target=lambda: asyncio.run(self._start_scheduler_with_notifications()),
            daemon=True
        )
        scheduler_thread.start()
        logger.info("[OK] Scheduler thread started")

        # Start bot - this will run immediately, not blocked by scheduler
        logger.info("\n[POLLING] Starting bot polling...")
        logger.info("Bot is running. Press Ctrl+C to stop.\n")

        try:
            # Use synchronous polling (not await)
            self.app.run_polling(allowed_updates=None)
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n[SHUTDOWN] Keyboard interrupt received")
        except (TimedOut, TimeoutError) as e:
            logger.error(f"\n[NETWORK] Telegram connection timed out: {type(e).__name__}")
            logger.error("This is likely due to ISP/network blocking Telegram API servers")
            logger.error("Solution: Use a VPN or configure a proxy in .env (TELEGRAM_PROXY=...)\n")
            logger.warning("[FALLBACK] Running in scraper-only mode - jobs are still being collected!")
            logger.warning("Scrapers will run every 6 hours and store jobs in the database.")
            logger.warning("Once you enable network access (VPN/Proxy), restart the bot to send Telegram messages.\n")

            # Keep the scheduler running even if Telegram is unavailable
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n[SHUTDOWN] Keyboard interrupt received")
        except Exception as e:
            logger.error(f"\n[ERROR] Unexpected error: {type(e).__name__}: {e}")
            logger.error("Bot will still continue running scrapers in fallback mode\n")

            # Keep the scheduler running even if there's an error
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n[SHUTDOWN] Keyboard interrupt received")

    async def _start_scheduler_with_notifications(self):
        """Start scheduler with integrated notifications."""
        async def scheduled_job_with_notifications():
            """Run scrapers then send group notifications for every new job."""
            logger.info("\n[SCHEDULED] Running periodic scrape...")
            result = await self.scheduler.run_all_scrapers()

            if result.get("new", 0) > 0:
                logger.info(f"[SCHEDULED] {result['new']} new jobs — sending group notifications...")
                db = SessionLocal()
                from db.models import Job

                new_jobs = db.query(Job).filter(
                    Job.created_at >= result["timestamp"],
                    Job.is_active == True,
                ).all()

                if new_jobs and self.notification_manager:
                    notify_result = await self.notification_manager.notify_all_new_jobs(new_jobs)
                    logger.info(
                        f"[SCHEDULED] Notifications: {notify_result['total_sent']} sent, "
                        f"{notify_result['total_failed']} failed"
                    )

                db.close()

        # START SCHEDULER IMMEDIATELY (don't wait for initial scrape)
        try:
            self.scheduler.scheduler.remove_job("scrape_all_sites")
        except Exception:
            pass

        self.scheduler.scheduler.add_job(
            scheduled_job_with_notifications,
            "interval",
            hours=6,
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

        # Handle notifications if we got new jobs
        if result.get("new", 0) > 0:
            logger.info(f"[STARTUP] {result['new']} new jobs found, sending notifications...")
            db = SessionLocal()
            from db.models import Job
            new_jobs = db.query(Job).filter(Job.created_at >= result["timestamp"]).all()

            if new_jobs and self.notification_manager:
                notify_result = await self.notification_manager.notify_all_new_jobs(new_jobs)
                logger.info(f"[STARTUP] Notifications: {notify_result['total_sent']} sent, "
                           f"{notify_result['total_failed']} failed")

            db.close()

        logger.info(f"[STARTUP] Initial scrape complete: {result['new']} new, {result['updated']} updated")

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
