from typing import List, Dict
from datetime import datetime, timedelta
from db.models import Job


def format_job_card(job: Job) -> str:
    """Format a job as a detailed card."""
    parts = []

    # Title
    parts.append(f"<b>{job.title}</b>")

    # Company and coin
    coin_text = f" ({job.coin_ticker})" if job.coin_ticker else ""
    parts.append(f"💼 {job.company}{coin_text}")

    # Location
    if job.location:
        parts.append(f"📍 {job.location}")

    # Listed date
    if job.listed_date:
        listed = job.listed_date.strftime("%b %d, %Y")
        parts.append(f"📅 Listed: {listed}")

    # Deadline
    if job.deadline:
        deadline = job.deadline.strftime("%b %d, %Y")
        days_left = (job.deadline - datetime.utcnow()).days
        if days_left > 0:
            parts.append(f"⏳ Deadline: {deadline} ({days_left} days left)")
        else:
            parts.append(f"⏳ Deadline: {deadline} (expired)")

    # Source
    parts.append(f"🌐 Source: {job.source_site}")

    # Link
    parts.append(f"<a href='{job.url}'>View Job</a>")

    return "\n".join(parts)


def format_jobs_list(jobs: List[Job], title: str = "") -> str:
    """Format a list of jobs with numbering."""
    if not jobs:
        return "No jobs found."

    lines = []
    if title:
        lines.append(f"<b>{title}</b>\n")

    for i, job in enumerate(jobs, 1):
        # Emoji numbers
        emoji = f"{i}️⃣"
        coin_text = f" [{job.coin_ticker}]" if job.coin_ticker else ""
        line = f"{emoji} <b>{job.title}</b> @ {job.company}{coin_text}"
        lines.append(line)

    return "\n".join(lines)


def format_new_jobs(jobs: List[Job]) -> str:
    """Format jobs for /new command (last 30 days)."""
    if not jobs:
        return "✨ No new jobs in the last 30 days"

    title = f"✨ <b>New Jobs (Last 30 Days)</b> — {len(jobs)} total\n"
    parts = [title]

    for i, job in enumerate(jobs, 1):
        emoji = f"{i}️⃣"
        coin = f"[{job.coin_ticker}]" if job.coin_ticker else ""
        created = job.created_at.strftime("%H:%M")
        part = f"{emoji} <b>{job.title}</b>\n   💼 {job.company} {coin} @ {created}"
        parts.append(part)

    return "\n".join(parts)


def format_expiring_jobs(jobs: List[Job]) -> str:
    """Format jobs for /expiring command."""
    if not jobs:
        return "⏰ No jobs expiring in the next 48 hours"

    title = f"⏰ <b>Jobs Expiring Soon</b> — {len(jobs)} deadlines in 48h\n"
    parts = [title]

    for i, job in enumerate(jobs, 1):
        emoji = f"{i}️⃣"
        coin = f"[{job.coin_ticker}]" if job.coin_ticker else ""
        hours_left = max(0, int((job.deadline - datetime.utcnow()).total_seconds() / 3600))
        part = f"{emoji} <b>{job.title}</b>\n   ⏳ {job.company} {coin} — {hours_left}h left"
        parts.append(part)

    return "\n".join(parts)


def format_subscriptions(subs: List[str]) -> str:
    """Format subscription list."""
    if not subs:
        return "📋 <b>Your Subscriptions</b>\n\nNo active subscriptions. Use /subscribe to start."

    lines = ["📋 <b>Your Subscriptions</b>\n"]
    for coin in sorted(subs):
        lines.append(f"• {coin}")

    return "\n".join(lines)


def format_job_for_group(job: Job) -> str:
    """Format job notification for group chat."""
    coin_text = job.coin_ticker if job.coin_ticker else "MISC"
    listed_text = job.listed_date.strftime("%b %d, %Y") if job.listed_date else datetime.utcnow().strftime("%b %d, %Y")
    deadline_text = job.deadline.strftime("%b %d, %Y") if job.deadline else "Open"

    return (
        f"<b>New job available for {coin_text}</b>\n\n"
        f"<b>{job.title}</b>\n"
        f"<b>Company:</b> {job.company}\n"
        f"<b>Location:</b> {job.location or 'Remote'}\n"
        f"<b>Listed:</b> {listed_text}\n"
        f"<b>Deadline:</b> {deadline_text}\n"
        f"<b>Source:</b> {job.source_site}\n\n"
        f'<a href="{job.url}">View Full Job</a>'
    )


def format_jobs_by_coin(grouped_jobs: Dict[str, List[Job]]) -> List[str]:
    """
    Format jobs grouped by coin. Returns a list of messages (split to stay
    under Telegram's 4096-char limit).
    """
    if not grouped_jobs:
        return ["No jobs available yet."]

    total_jobs = sum(len(jobs) for jobs in grouped_jobs.values())
    messages = []
    current = [f"<b>Available Jobs by Coin</b> - {total_jobs} total jobs\n"]

    for coin, jobs in grouped_jobs.items():
        block = [f"\n<b>{coin}</b> ({len(jobs)} jobs)", "-" * 30]
        for idx, job in enumerate(jobs, 1):
            title = job.title[:50] if len(job.title) > 50 else job.title
            listed = job.listed_date.strftime("%b %d") if job.listed_date else ""
            date_tag = f" | {listed}" if listed else ""
            block.append(f"{idx}. <b>{title}</b>\n   {job.company}{date_tag}")

        block_text = "\n".join(block)

        # Split into new message if adding this block would exceed 4000 chars
        current_text = "\n".join(current)
        if len(current_text) + len(block_text) > 3800:
            messages.append(current_text)
            current = [block_text]
        else:
            current.append(block_text)

    footer = f"\n<i>Total: {total_jobs} active jobs across {len(grouped_jobs)} coins</i>"
    current_text = "\n".join(current)
    if len(current_text) + len(footer) > 3800:
        messages.append(current_text)
        messages.append(footer)
    else:
        messages.append(current_text + footer)

    return messages


def format_coin_statistics(coin_counts: Dict[str, int]) -> str:
    """Format coin statistics showing job counts per coin."""
    if not coin_counts:
        return "No jobs available yet."

    total_jobs = sum(coin_counts.values())
    lines = [f"<b>Jobs Available by Coin</b> — {total_jobs} total jobs\n"]

    for idx, (coin, count) in enumerate(coin_counts.items(), 1):
        emoji = f"{idx}️⃣"
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        lines.append(f"{emoji} <b>{coin}</b>: {count} jobs ({percentage:.1f}%)")

    lines.append(f"\n<i>Total: {total_jobs} active jobs across {len(coin_counts)} coins</i>")
    return "\n".join(lines)


def format_start_message() -> str:
    """Format the /start welcome message."""
    return """
<b>Welcome to Crypto Jobs Bot!</b> 🤖

I help you find crypto jobs matching your interests. Subscribe to coins and get notified of new opportunities.

<b>Available Commands:</b>

📌 <b>/start</b> — Show this message
🪙 <b>/coin BTC</b> — Jobs for a specific coin (e.g., /coin ETH, /coin LINK)
✨ <b>/new</b> — New jobs from last 30 days
⏰ <b>/expiring</b> — Jobs expiring in next 48 hours
📊 <b>/jobs</b> — View available jobs per coin
🔔 <b>/subscribe COIN</b> — Subscribe to a coin (e.g., /subscribe ETH)
🔕 <b>/unsubscribe COIN</b> — Unsubscribe from a coin
📋 <b>/mysubs</b> — View your subscriptions

<i>Tip: Type /coin BTC to see what coins are available!</i>
""".strip()
