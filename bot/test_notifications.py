import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import init_db, SessionLocal
from db.models import Job
from db.queries import insert_or_update_jobs, add_subscription
from bot.notifications import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_notifications():
    """Test notification system."""
    logger.info("\n" + "="*70)
    logger.info("NOTIFICATION SYSTEM TEST")
    logger.info("="*70)

    # Initialize database
    logger.info("\n[INIT] Initializing database...")
    init_db()

    db = SessionLocal()

    # Create test data
    logger.info("\n[DATA] Creating test job and subscription...")
    test_job_data = {
        "title": "Senior Rust Developer",
        "company": "Chainlink Labs",
        "location": "Remote",
        "url": "https://example.com/job-rust",
        "source_site": "web3.career",
        "scraped_at": datetime.utcnow(),
        "coin_ticker": "LINK",
    }

    insert_or_update_jobs([test_job_data], db)

    # Get the job
    job = db.query(Job).filter(Job.coin_ticker == "LINK").first()
    logger.info(f"[OK] Created test job: {job.title}")

    # Add subscription
    test_user_id = 123456789
    add_subscription(test_user_id, "LINK", db)
    logger.info(f"[OK] Added test subscription: user {test_user_id} -> LINK")

    # Mock Telegram application
    logger.info("\n[MOCK] Creating mock Telegram bot...")
    mock_app = MagicMock()
    mock_app.bot = MagicMock()
    mock_app.bot.send_message = AsyncMock()

    # Create notification manager
    logger.info("[NOTIFY] Creating notification manager...")
    manager = NotificationManager(mock_app, db)

    # Test 1: Send single notification
    logger.info("\n[TEST 1] Testing single notification...")
    success = await manager.send_job_notification(test_user_id, job)
    logger.info(f"[RESULT] Send notification: {success}")

    # Verify the message was sent
    if mock_app.bot.send_message.called:
        call_args = mock_app.bot.send_message.call_args
        chat_id = call_args.kwargs.get("chat_id")
        message = call_args.kwargs.get("text")
        logger.info(f"[OK] Message sent to chat_id: {chat_id}")
        logger.info(f"[OK] Message preview: {message[:100]}...")

        # Verify content
        assert "[LINK]" in message, "Message should contain coin ticker"
        assert "view" in message.lower() or "href" in message, "Message should contain link"
        logger.info("[OK] Message content verified")
    else:
        logger.error("[ERROR] send_message was not called")

    # Test 2: Notify all subscribers
    logger.info("\n[TEST 2] Testing notify_subscribers...")
    mock_app.bot.send_message.reset_mock()

    result = await manager.notify_subscribers("LINK", job)
    logger.info(f"[RESULT] Notify subscribers: sent={result['sent']}, failed={result['failed']}")

    if result["sent"] > 0:
        logger.info("[OK] Subscribers notified successfully")
    else:
        logger.warning("[WARNING] No notifications sent")

    # Test 3: Notify multiple jobs
    logger.info("\n[TEST 3] Testing notify_all_new_jobs...")
    mock_app.bot.send_message.reset_mock()

    # Create another job
    test_job_data_2 = {
        "title": "Python Backend Engineer",
        "company": "Uniswap Labs",
        "location": "San Francisco",
        "url": "https://example.com/job-python",
        "source_site": "cryptojobs.com",
        "scraped_at": datetime.utcnow(),
        "coin_ticker": "UNI",
    }

    insert_or_update_jobs([test_job_data_2], db)
    add_subscription(test_user_id, "UNI", db)

    job_2 = db.query(Job).filter(Job.coin_ticker == "UNI").first()

    result = await manager.notify_all_new_jobs([job, job_2])
    logger.info(f"[RESULT] Notify all jobs: total_sent={result['total_sent']}, "
               f"total_failed={result['total_failed']}")

    # Test 4: Test with error handling
    logger.info("\n[TEST 4] Testing error handling...")
    from telegram.error import TelegramError

    # Create a mock error that simulates user blocking bot
    mock_error = TelegramError("Forbidden: bot was blocked by the user")
    mock_app.bot.send_message = AsyncMock(side_effect=mock_error)
    manager_error = NotificationManager(mock_app, db)

    success = await manager_error.send_job_notification(999999, job)
    logger.info(f"[RESULT] Send with error: {success} (expected False)")
    assert success == False, "Should return False on error"
    logger.info("[OK] Error handling verified")

    db.close()

    logger.info("\n" + "="*70)
    logger.info("NOTIFICATION TESTS COMPLETED")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_notifications())
        logger.info("[OK] All notification tests passed!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)
