from typing import List
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
    """Format jobs for /new command."""
    if not jobs:
        return "✨ No new jobs in the last 24 hours"

    title = f"✨ <b>New Jobs (Last 24h)</b> — {len(jobs)} total\n"
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
    deadline_text = job.deadline.strftime("%b %d, %Y") if job.deadline else "No deadline"
    listed_text = job.listed_date.strftime("%b %d, %Y") if job.listed_date else "Unknown"
    coin_text = job.coin_ticker if job.coin_ticker else "MISC"

    return f"""<b>🆕 {coin_text}</b> | {job.title}

<b>💼 Company:</b> {job.company}
<b>📍 Location:</b> {job.location}
<b>📅 Posted:</b> {listed_text}
<b>⏳ Deadline:</b> {deadline_text}
<b>📌 Source:</b> {job.source_site}

<a href="{job.url}">View Full Job</a>"""


def format_start_message() -> str:
    """Format the /start welcome message."""
    return """
<b>Welcome to Crypto Jobs Bot!</b> 🤖

I help you find crypto jobs matching your interests. Subscribe to coins and get notified of new opportunities.

<b>Available Commands:</b>

📌 <b>/start</b> — Show this message
🪙 <b>/coin BTC</b> — Jobs for a specific coin (e.g., /coin ETH, /coin LINK)
✨ <b>/new</b> — New jobs from last 24 hours
⏰ <b>/expiring</b> — Jobs expiring in next 48 hours
🔔 <b>/subscribe COIN</b> — Subscribe to a coin (e.g., /subscribe ETH)
🔕 <b>/unsubscribe COIN</b> — Unsubscribe from a coin
📋 <b>/mysubs</b> — View your subscriptions

<i>Tip: Type /coin BTC to see what coins are available!</i>
""".strip()
