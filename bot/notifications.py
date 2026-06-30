import asyncio
import logging
import os
from typing import List, Dict
from telegram.ext import Application
from telegram.error import TelegramError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from db.models import Job
from db.queries import get_subscribers_for_coin

load_dotenv()

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages sending job notifications to group chat and users."""

    def __init__(self, app: Application, db: Session):
        """Initialize with Telegram bot application and database session."""
        self.app = app
        self.db = db
        self.delay_between_sends = 0.2  # seconds, to avoid rate limiting
        self.group_chat_id = int(os.getenv("GROUP_CHAT_ID", 0))

    async def send_job_to_group(self, job: Job) -> bool:
        """Send job notification to group chat."""
        try:
            if not self.group_chat_id:
                logger.error("GROUP_CHAT_ID not set in .env")
                return False

            from bot.formatters import format_job_for_group
            message = format_job_for_group(job)

            await self.app.bot.send_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            logger.info(f"[GROUP] Sent to group: {job.title[:50]}...")
            return True

        except Exception as e:
            logger.error(f"[GROUP] Failed to send to group: {str(e)}")
            return False

    async def send_job_notification(self, user_id: int, job: Job) -> bool:
        """
        Send a job notification to a user.

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format message
            coin_badge = f"[{job.coin_ticker}]" if job.coin_ticker else "[Unmatched]"
            message = (
                f"<b>🆕 New Job {coin_badge}</b>\n\n"
                f"<b>{job.title}</b>\n"
                f"💼 {job.company}\n"
                f"📍 {job.location}\n"
                f"🌐 {job.source_site}\n"
                f"\n"
                f'<a href="{job.url}">View Full Job</a>'
            )

            # Send message
            await self.app.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            logger.info(f"[NOTIFY] Sent to user {user_id}: {job.title[:50]}...")
            return True

        except TelegramError as e:
            error_str = str(e)
            if "blocked" in error_str.lower():
                logger.warning(f"[NOTIFY] User {user_id} blocked the bot")
            elif "not found" in error_str.lower():
                logger.warning(f"[NOTIFY] User {user_id} not found")
            else:
                logger.error(f"[NOTIFY] Telegram error for user {user_id}: {error_str}")
            return False
        except Exception as e:
            logger.error(f"[NOTIFY] Error sending to user {user_id}: {str(e)}")
            return False

    async def notify_subscribers(self, coin_ticker: str, job: Job) -> Dict[str, int]:
        """
        Send notification about a job to all subscribers of a coin.

        Returns:
            {"sent": count, "failed": count}
        """
        try:
            subscribers = get_subscribers_for_coin(coin_ticker, self.db)
            logger.info(f"[NOTIFY] Found {len(subscribers)} subscribers for {coin_ticker}")

            sent = 0
            failed = 0

            for user_id in subscribers:
                success = await self.send_job_notification(user_id, job)

                if success:
                    sent += 1
                else:
                    failed += 1

                # Add delay to avoid rate limiting
                await asyncio.sleep(self.delay_between_sends)

            logger.info(f"[NOTIFY] {coin_ticker}: Sent {sent}, Failed {failed}")
            return {"sent": sent, "failed": failed}

        except Exception as e:
            logger.error(f"[NOTIFY] Error notifying subscribers for {coin_ticker}: {str(e)}")
            return {"sent": 0, "failed": 0}

    async def notify_all_new_jobs(self, new_jobs: List[Job]) -> Dict[str, int]:
        """
        Send notifications for all new jobs to group chat and subscribers.

        Returns:
            {"total_sent": int, "total_failed": int}
        """
        if not new_jobs:
            logger.info("[NOTIFY] No new jobs to notify")
            return {"total_sent": 0, "total_failed": 0}

        logger.info(f"[NOTIFY] Processing {len(new_jobs)} new jobs for group notifications")

        total_sent = 0
        total_failed = 0

        for job in new_jobs:
            # Send to group chat
            if await self.send_job_to_group(job):
                total_sent += 1
            else:
                total_failed += 1

            # Also send to individual subscribers if coin is matched
            if job.coin_ticker:
                result = await self.notify_subscribers(job.coin_ticker, job)
                total_sent += result["sent"]
                total_failed += result["failed"]

            await asyncio.sleep(self.delay_between_sends)

        logger.info(f"[NOTIFY] Totals: {total_sent} sent, {total_failed} failed")
        return {"total_sent": total_sent, "total_failed": total_failed}
