from typing import List, Dict, Optional
from datetime import datetime, timedelta
from db.models import Job

_LIMIT = 3800  # stay under Telegram's 4096-char hard limit


def _flush(pages: List[str], buf: List[str]) -> None:
    """Append current buffer to pages and clear it."""
    if buf:
        pages.append("\n".join(buf))
        buf.clear()


# ---------------------------------------------------------------------------
# /jobs  — compact coin summary list
# ---------------------------------------------------------------------------

def format_jobs_by_coin(grouped_jobs: Dict[str, List[Job]]) -> List[str]:
    """
    /jobs  — one line per coin showing the count.
    Example:
        BTC  -  8 jobs
        ETH  -  5 jobs
    Returns List[str] split to stay under Telegram limit.
    """
    if not grouped_jobs:
        return ["No jobs available yet. The scraper runs every 60 minutes.\n\nTry again shortly."]

    total = sum(len(v) for v in grouped_jobs.values())
    pages: List[str] = []
    buf: List[str] = [
        f"<b>Available Coins</b>  -  {total} jobs across {len(grouped_jobs)} coins\n",
        "<i>Use /coin TICKER to see all jobs for a coin</i>\n",
    ]

    for coin, jobs in grouped_jobs.items():
        line = f"<b>{coin}</b>  -  {len(jobs)} job{'s' if len(jobs) != 1 else ''}"
        if len("\n".join(buf)) + len(line) + 1 > _LIMIT:
            _flush(pages, buf)
        buf.append(line)

    _flush(pages, buf)
    return pages


# ---------------------------------------------------------------------------
# /coin BTC  — full job cards for one coin
# ---------------------------------------------------------------------------

def format_jobs_list(jobs: List[Job], title: str = "") -> List[str]:
    """
    /coin BTC  — detailed listing: title, company, listed date, apply link.
    Returns List[str] split to stay under Telegram limit.
    """
    if not jobs:
        coin = title.split()[0] if title else "this coin"
        return [
            f"<b>{title}</b>\n\nNo active jobs found.\n\n"
            f"Use /jobs to see which coins have listings."
        ]

    pages: List[str] = []
    buf: List[str] = [f"<b>{title}</b>\n"] if title else []

    for i, job in enumerate(jobs, 1):
        title_text = job.title if len(job.title) <= 60 else job.title[:57] + "..."
        listed = job.listed_date.strftime("%b %d, %Y") if job.listed_date else ""
        date_line = f"   Listed: {listed}" if listed else ""
        apply_line = f'   <a href="{job.url}">Apply</a>' if job.url else ""

        entry_lines = [
            f"{i}. <b>{title_text}</b>",
            f"   Company: {job.company}",
        ]
        if date_line:
            entry_lines.append(date_line)
        if apply_line:
            entry_lines.append(apply_line)

        entry = "\n".join(entry_lines)

        if len("\n".join(buf)) + len(entry) + 2 > _LIMIT:
            _flush(pages, buf)
        buf.append(entry)
        buf.append("")  # blank line between jobs

    _flush(pages, buf)
    return pages


# ---------------------------------------------------------------------------
# /new  — recent jobs grouped by coin
# ---------------------------------------------------------------------------

def format_new_jobs(jobs: List[Job], max_per_coin: int = 5) -> List[str]:
    """
    /new  — coin-mapped jobs listed in last 30 days, grouped by coin.
    Only shows jobs with a known coin ticker (skips unmapped/general jobs).
    Max 5 jobs per coin to keep messages short.
    Returns List[str] split to stay under Telegram limit.
    """
    # Keep only coin-mapped jobs
    coin_jobs = [j for j in jobs if j.coin_ticker]

    if not coin_jobs:
        return [
            "<b>New Jobs (Last 30 Days)</b>\n\n"
            "No new coin-specific jobs found.\n\n"
            "<i>Use /jobs to see all available coins.</i>"
        ]

    # Group by coin, sorted alphabetically
    groups: Dict[str, List[Job]] = {}
    for job in coin_jobs:
        groups.setdefault(job.coin_ticker, []).append(job)
    ordered = sorted(groups.keys())

    total_coins = len(groups)
    total_shown = sum(min(len(v), max_per_coin) for v in groups.values())
    total_all = len(coin_jobs)

    pages: List[str] = []
    buf: List[str] = [
        f"<b>New Jobs (Last 30 Days)</b>  -  {total_all} jobs across {total_coins} coins\n"
    ]

    for coin in ordered:
        jobs_for_coin = groups[coin]
        shown = jobs_for_coin[:max_per_coin]
        extra = len(jobs_for_coin) - max_per_coin

        header = f"\n<b>[{coin}]</b>"
        if len("\n".join(buf)) + len(header) + 1 > _LIMIT:
            _flush(pages, buf)
        buf.append(header)

        for i, job in enumerate(shown, 1):
            title_text = job.title if len(job.title) <= 60 else job.title[:57] + "..."
            listed = job.listed_date.strftime("%b %d, %Y") if job.listed_date else ""
            apply_tag = f' | <a href="{job.url}">Apply</a>' if job.url else ""
            entry = (
                f"{i}. <b>{title_text}</b>\n"
                f"   {job.company}"
                + (f" | {listed}" if listed else "")
                + apply_tag
            )
            if len("\n".join(buf)) + len(entry) + 2 > _LIMIT:
                _flush(pages, buf)
            buf.append(entry)

        if extra > 0:
            more = f"   <i>+{extra} more  -  use /coin {coin}</i>"
            buf.append(more)

    _flush(pages, buf)
    return pages


# ---------------------------------------------------------------------------
# /upcoming  — jobs listed in the last 7 days, grouped by day
# ---------------------------------------------------------------------------

def format_upcoming_jobs(jobs: List[Job], max_per_day: int = 10) -> List[str]:
    """
    /upcoming  — recent listings grouped by day (Today, Yesterday, X days ago).
    Capped at max_per_day per group to keep messages short.
    Returns List[str] split to stay under Telegram limit.
    """
    if not jobs:
        return [
            "<b>Recent Job Listings (Last 7 Days)</b>\n\n"
            "No new jobs found in the last 7 days.\n\n"
            "<i>Scrapers run every 6 hours. Check back soon.</i>"
        ]

    today = datetime.utcnow().date()

    # Group by day offset (0=today, 1=yesterday, …)
    groups: Dict[int, List[Job]] = {}
    for job in jobs:
        offset = (today - job.listed_date.date()).days if job.listed_date else 0
        if 0 <= offset <= 6:
            groups.setdefault(offset, []).append(job)

    total = sum(len(v) for v in groups.values())
    pages: List[str] = []
    buf: List[str] = [f"<b>Recent Job Listings (Last 7 Days)</b>  -  {total} jobs\n"]

    for offset in sorted(groups.keys()):
        day_jobs = groups[offset]
        shown = day_jobs[:max_per_day]
        extra = len(day_jobs) - max_per_day

        if offset == 0:
            day_label = "Today"
        elif offset == 1:
            day_label = "Yesterday"
        else:
            day_label = f"{offset} days ago"

        header = f"\n<b>{day_label}</b>  -  {len(day_jobs)} job{'s' if len(day_jobs) != 1 else ''}"
        if len("\n".join(buf)) + len(header) + 1 > _LIMIT:
            _flush(pages, buf)
        buf.append(header)

        for i, job in enumerate(shown, 1):
            title_text = job.title if len(job.title) <= 60 else job.title[:57] + "..."
            coin_tag = f" [{job.coin_ticker}]" if job.coin_ticker else ""
            listed = job.listed_date.strftime("%b %d") if job.listed_date else "Unknown"
            apply_tag = f' | <a href="{job.url}">Apply</a>' if job.url else ""
            entry = (
                f"{i}. <b>{title_text}</b>{coin_tag}\n"
                f"   {job.company} | Listed: {listed}"
                + apply_tag
            )
            if len("\n".join(buf)) + len(entry) + 2 > _LIMIT:
                _flush(pages, buf)
            buf.append(entry)

        if extra > 0:
            buf.append(f"   <i>+{extra} more — use /new to see all</i>")

    _flush(pages, buf)
    return pages


# ---------------------------------------------------------------------------
# /expiring  — jobs with deadline or old listings
# ---------------------------------------------------------------------------

def format_expiring_jobs(jobs: List[Job]) -> List[str]:
    """
    /expiring  — jobs expiring within 30 days.
    Returns List[str] split to stay under Telegram limit.
    """
    if not jobs:
        return [
            "<b>Jobs Expiring (Next 30 Days)</b>\n\n"
            "No jobs expiring in the next 30 days."
        ]

    pages: List[str] = []
    buf: List[str] = [f"<b>Jobs Expiring (Next 30 Days)</b>  -  {len(jobs)} listings\n"]

    for i, job in enumerate(jobs, 1):
        title_text = job.title if len(job.title) <= 60 else job.title[:57] + "..."
        coin = f"[{job.coin_ticker}]" if job.coin_ticker else ""

        if job.deadline:
            days_left = max(0, (job.deadline - datetime.utcnow()).days)
            time_label = f"Deadline: {job.deadline.strftime('%b %d, %Y')}  ({days_left}d left)"
        elif job.listed_date:
            age = (datetime.utcnow() - job.listed_date).days
            est_left = max(0, 30 - age)
            time_label = f"Listed {age}d ago  -  est. {est_left}d remaining"
        else:
            time_label = "Age unknown"

        apply_tag = f'\n   <a href="{job.url}">Apply</a>' if job.url else ""
        entry = (
            f"{i}. <b>{title_text}</b> {coin}\n"
            f"   {job.company}\n"
            f"   {time_label}"
            + apply_tag
        )

        if len("\n".join(buf)) + len(entry) + 2 > _LIMIT:
            _flush(pages, buf)
        buf.append(entry)
        buf.append("")

    _flush(pages, buf)
    return pages


# ---------------------------------------------------------------------------
# Group notifications
# ---------------------------------------------------------------------------

def format_job_for_group(job: Job) -> str:
    """Format new-job notification for group chat."""
    coin_text = job.coin_ticker if job.coin_ticker else "Crypto"
    listed = job.listed_date.strftime("%b %d, %Y") if job.listed_date else datetime.utcnow().strftime("%b %d, %Y")
    return (
        f"<b>New job available  [{coin_text}]</b>\n\n"
        f"<b>{job.title}</b>\n"
        f"Company: {job.company}\n"
        f"Location: {job.location or 'Remote'}\n"
        f"Listed: {listed}\n"
        f"Source: {job.source_site}\n\n"
        f'<a href="{job.url}">View Full Job</a>'
    )


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def format_job_card(job: Job) -> str:
    """Detailed single-job card (used internally)."""
    coin_text = f" ({job.coin_ticker})" if job.coin_ticker else ""
    listed = job.listed_date.strftime("%b %d, %Y") if job.listed_date else ""
    parts = [
        f"<b>{job.title}</b>",
        f"Company: {job.company}{coin_text}",
    ]
    if job.location:
        parts.append(f"Location: {job.location}")
    if listed:
        parts.append(f"Listed: {listed}")
    if job.deadline:
        days = (job.deadline - datetime.utcnow()).days
        parts.append(f"Deadline: {job.deadline.strftime('%b %d, %Y')} ({max(0,days)}d left)")
    parts.append(f"Source: {job.source_site}")
    parts.append(f'<a href="{job.url}">Apply</a>')
    return "\n".join(parts)


def format_subscriptions(subs: List[str]) -> str:
    if not subs:
        return (
            "<b>Your Subscriptions</b>\n\n"
            "No active subscriptions.\n"
            "Use /subscribe COIN to get notified of new jobs."
        )
    lines = ["<b>Your Subscriptions</b>\n"]
    for coin in sorted(subs):
        lines.append(f"- {coin}")
    lines.append("\nUse /unsubscribe COIN to remove one.")
    return "\n".join(lines)


def format_coin_statistics(coin_counts: Dict[str, int]) -> str:
    if not coin_counts:
        return "No jobs available yet."
    total = sum(coin_counts.values())
    lines = [f"<b>Jobs by Coin</b>  -  {total} total\n"]
    for coin, count in coin_counts.items():
        lines.append(f"<b>{coin}</b>  -  {count} jobs")
    return "\n".join(lines)


def format_start_message() -> str:
    return (
        "<b>Crypto Jobs Bot</b>\n\n"
        "I scrape 58+ crypto/blockchain accounts every 4 hours and group jobs by coin.\n\n"
        "<b>Commands:</b>\n"
        "/jobs  -  List all coins with job counts\n"
        "/coin BTC  -  All Bitcoin jobs (title, company, <b>date listed</b>, apply link)\n"
        "/new  -  Jobs listed in the last 30 days, grouped by coin\n"
        "/upcoming  -  Jobs posted in the last 7 days, grouped by day (with <b>date</b>)\n"
        "/expiring  -  Jobs expiring in the next 30 days\n"
        "/subscribe ETH  -  Get notified when new ETH jobs appear\n"
        "/unsubscribe ETH  -  Stop ETH notifications\n"
        "/mysubs  -  See your active subscriptions\n\n"
        "<i>Example: /coin LINK shows all Chainlink jobs available right now.</i>"
    )
