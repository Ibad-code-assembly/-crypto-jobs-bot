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
    # Hot coin alerts (>4 jobs for same coin)
    # ------------------------------------------------------------------

    async def send_hot_coin_alert(self, coin_ticker: str, jobs: List[Job], date_str: str = None) -> bool:
        """
        Send a special highlighted alert for coins with 4+ jobs listed on the same date.
        This is sent BEFORE the regular digest.
        """
        if not self.group_chat_id or len(jobs) < 4:
            return False

        # Create exciting alert message
        lines = [
            f"🔥 <b>HOT: {coin_ticker} is HIRING!</b> 🔥",
            f"<b>{len(jobs)} NEW POSITIONS</b> for <b>{coin_ticker}</b>",
        ]

        # Show the date if provided
        if date_str:
            lines.append(f"Posted on: <b>{date_str}</b>")

        lines.append(f"Massive hiring activity detected!\n")

        # List top jobs
        shown = 0
        max_show = 8
        for job in jobs[:max_show]:
            title = job.title if len(job.title) <= 50 else job.title[:47] + "..."
            lines.append(f"  ✓ <b>{title}</b> @ {job.company}")
            shown += 1

        if len(jobs) > max_show:
            lines.append(f"\n  ...and <b>{len(jobs) - max_show} more positions</b>!")

        lines.append(f"\n💼 Use <b>/coin {coin_ticker}</b> to see all jobs!")

        message = "\n".join(lines)

        try:
            await self.app.bot.send_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"[NOTIFY] 🔥 Hot coin alert: {coin_ticker} with {len(jobs)} jobs on {date_str}")
            return True
        except Exception as e:
            logger.error(f"[NOTIFY] Failed to send hot coin alert for {coin_ticker}: {e}")
            return False

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
    # New coin listing alerts
    # ------------------------------------------------------------------

    async def send_new_coins_alert(self, new_coins: List) -> bool:
        """
        Send alert about new coins listed on exchanges.
        Grouped by exchange.
        """
        if not self.group_chat_id or not new_coins:
            return False

        # Group coins by exchange
        by_exchange: Dict[str, List] = {}
        for coin in new_coins[:30]:  # Limit to 30 most recent
            for exchange in coin.exchanges.split(","):
                by_exchange.setdefault(exchange, []).append(coin)

        lines = [
            f"🪙 <b>New Coin Listings!</b>  -  {len(new_coins)} coins across {len(by_exchange)} exchanges\n"
        ]

        shown = 0
        for exchange in sorted(by_exchange.keys()):
            coins_on_ex = by_exchange[exchange]
            lines.append(f"<b>{exchange}</b>: {len(coins_on_ex)} coins")
            for coin in coins_on_ex[:5]:  # Show first 5 per exchange
                pairs = coin.trading_pairs.split(",")[:2] if coin.trading_pairs else ["USDT"]
                lines.append(f"  • <b>{coin.coin_symbol}</b> ({', '.join(pairs)})")
                shown += 1

            if len(coins_on_ex) > 5:
                lines.append(f"  ...and {len(coins_on_ex) - 5} more")

        lines.append(f"\n💰 Use <b>/newcoins</b> to see all new listings!")

        message = "\n".join(lines)

        try:
            await self.app.bot.send_message(
                chat_id=self.group_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"[NOTIFY] 🪙 New coins alert: {len(new_coins)} coins across {len(by_exchange)} exchanges")
            return True
        except Exception as e:
            logger.error(f"[NOTIFY] Failed to send new coins alert: {e}")
            return False

    # ------------------------------------------------------------------
    # Main entry point called by scheduler
    # ------------------------------------------------------------------

    async def notify_all_new_jobs(self, new_jobs: List[Job]) -> Dict[str, int]:
        """
        Called after each scrape with the list of newly inserted jobs.
        1. Detects "hot coins" (4+ jobs listed on same date) and sends special alerts
        2. Sends one digest to the group chat.
        3. DMs individual subscribers per coin.
        """
        if not new_jobs:
            return {"total_sent": 0, "total_failed": 0}

        logger.info(f"[NOTIFY] {len(new_jobs)} new jobs — sending notifications")

        # Group jobs by coin to detect hot coins
        coin_jobs = [j for j in new_jobs if j.coin_ticker]
        by_coin: Dict[str, List[Job]] = {}
        for job in coin_jobs:
            by_coin.setdefault(job.coin_ticker, []).append(job)

        # 1. Send special alerts for hot coins (4+ jobs listed on same date)
        hot_coins_by_date: Dict[str, Dict[str, List[Job]]] = {}  # coin -> {date -> [jobs]}

        for coin_ticker, jobs_for_coin in by_coin.items():
            # Group this coin's jobs by listing date
            by_date: Dict[str, List[Job]] = {}
            for job in jobs_for_coin:
                date_str = job.listed_date.strftime("%Y-%m-%d") if job.listed_date else "Unknown"
                by_date.setdefault(date_str, []).append(job)

            # Check if any date has 4+ jobs for this coin
            hot_dates = {date: jobs for date, jobs in by_date.items() if len(jobs) >= 4}
            if hot_dates:
                hot_coins_by_date[coin_ticker] = hot_dates

        if hot_coins_by_date:
            logger.info(f"[NOTIFY] 🔥 Detected hot coins with 4+ jobs on same date")
            for coin_ticker in sorted(hot_coins_by_date.keys()):
                for date_str, jobs_on_date in sorted(hot_coins_by_date[coin_ticker].items()):
                    await self.send_hot_coin_alert(coin_ticker, jobs_on_date, date_str)
                    await asyncio.sleep(0.5)  # Stagger alerts

        # 2. Group digest (single message)
        await self.send_digest_to_group(new_jobs)

        # 3. DM individual subscribers for coin-mapped jobs
        total_sent = total_failed = 0
        for job in new_jobs:
            if job.coin_ticker:
                r = await self.notify_subscribers(job.coin_ticker, job)
                total_sent += r["sent"]
                total_failed += r["failed"]
            await asyncio.sleep(_DELAY)

        logger.info(f"[NOTIFY] DMs: {total_sent} sent, {total_failed} failed")
        return {"total_sent": total_sent, "total_failed": total_failed}
