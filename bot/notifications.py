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

_MAX_JOBS_IN_DIGEST = 20   # cap so the digest message stays readable
_DELAY = 0.3               # seconds between sends to avoid Telegram flood limit


class NotificationManager:
    """Sends job update digests to the group chat and individual subscribers."""

    def __init__(self, app: Application, db: Session):
        self.app = app
        self.db = db
        self.group_chat_id = int(os.getenv("GROUP_CHAT_ID", 0))

    # ------------------------------------------------------------------
    # Group digest
    # ------------------------------------------------------------------

    async def send_digest_to_group(self, new_jobs: List[Job]) -> bool:
        """
        Send one digest message to the group listing all new coin-mapped jobs.
        Groups jobs by coin ticker. Skips jobs with no coin mapping.
        """
        if not self.group_chat_id:
            logger.error("[NOTIFY] GROUP_CHAT_ID not set — cannot send group digest")
            return False

        # Only coin-mapped jobs
        coin_jobs = [j for j in new_jobs if j.coin_ticker]
        if not coin_jobs:
            logger.info("[NOTIFY] No coin-mapped new jobs — skipping group digest")
            return False

        # Group by coin
        by_coin: Dict[str, List[Job]] = {}
        for job in coin_jobs:
            by_coin.setdefault(job.coin_ticker, []).append(job)

        total = len(coin_jobs)
        coins = sorted(by_coin.keys())

        lines = [
            f"<b>New Jobs Alert!</b>  -  {total} new job{'s' if total != 1 else ''} "
            f"across {len(coins)} coin{'s' if len(coins) != 1 else ''}\n"
        ]

        shown = 0
        for coin in coins:
            jobs_for_coin = by_coin[coin]
            lines.append(f"<b>[{coin}]</b>  {len(jobs_for_coin)} job{'s' if len(jobs_for_coin) != 1 else ''}")
            for job in jobs_for_coin:
                if shown >= _MAX_JOBS_IN_DIGEST:
                    remaining = total - shown
                    lines.append(f"  ...and {remaining} more")
                    break
                title = job.title if len(job.title) <= 55 else job.title[:52] + "..."
                lines.append(f"  - <b>{title}</b> @ {job.company}")
                shown += 1

        lines.append(f"\n<i>Use /jobs to see all available coins or /coin TICKER for details.</i>")

        message = "\n".join(lines)

        try:
            await self.app.bot.send_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"[NOTIFY] Group digest sent: {total} new jobs across {len(coins)} coins")
            return True
        except Exception as e:
            logger.error(f"[NOTIFY] Failed to send group digest: {e}")
            return False

    # ------------------------------------------------------------------
    # Individual subscriber DMs
    # ------------------------------------------------------------------

    async def _send_dm(self, user_id: int, job: Job) -> bool:
        """Send one job notification DM to a subscriber."""
        try:
            coin_badge = f"[{job.coin_ticker}]" if job.coin_ticker else "[Crypto]"
            listed = job.listed_date.strftime("%b %d, %Y") if job.listed_date else ""
            text = (
                f"<b>New Job {coin_badge}</b>\n\n"
                f"<b>{job.title}</b>\n"
                f"Company: {job.company}\n"
                + (f"Listed: {listed}\n" if listed else "")
                + f"Source: {job.source_site}\n\n"
                f'<a href="{job.url}">View Job</a>'
            )
            await self.app.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return True
        except TelegramError as e:
            logger.warning(f"[NOTIFY] DM to {user_id} failed: {e}")
            return False
        except Exception as e:
            logger.error(f"[NOTIFY] Error DMing {user_id}: {e}")
            return False

    async def notify_subscribers(self, coin_ticker: str, job: Job) -> Dict[str, int]:
        """Notify all users subscribed to this coin."""
        subscribers = get_subscribers_for_coin(coin_ticker, self.db)
        sent = failed = 0
        for uid in subscribers:
            ok = await self._send_dm(uid, job)
            sent += ok
            failed += (1 - ok)
            await asyncio.sleep(_DELAY)
        return {"sent": sent, "failed": failed}

    # ------------------------------------------------------------------
    # Main entry point called by scheduler
    # ------------------------------------------------------------------

    async def notify_all_new_jobs(self, new_jobs: List[Job]) -> Dict[str, int]:
        """
        Called after each scrape with the list of newly inserted jobs.
        1. Sends one digest to the group chat.
        2. DMs individual subscribers per coin.
        """
        if not new_jobs:
            return {"total_sent": 0, "total_failed": 0}

        logger.info(f"[NOTIFY] {len(new_jobs)} new jobs — sending notifications")

        # 1. Group digest (single message)
        await self.send_digest_to_group(new_jobs)

        # 2. DM individual subscribers for coin-mapped jobs
        total_sent = total_failed = 0
        for job in new_jobs:
            if job.coin_ticker:
                r = await self.notify_subscribers(job.coin_ticker, job)
                total_sent += r["sent"]
                total_failed += r["failed"]
            await asyncio.sleep(_DELAY)

        logger.info(f"[NOTIFY] DMs: {total_sent} sent, {total_failed} failed")
        return {"total_sent": total_sent, "total_failed": total_failed}
