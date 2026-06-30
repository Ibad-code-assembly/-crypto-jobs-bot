import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import init_db, SessionLocal
from db.queries import insert_or_update_jobs
from bot.handlers import (
    start_handler,
    coin_handler,
    new_handler,
    expiring_handler,
)
from bot.formatters import (
    format_start_message,
    format_jobs_list,
    format_new_jobs,
)
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bot_structure():
    """Test bot initialization and handlers."""
    logger.info("\n" + "="*70)
    logger.info("BOT STRUCTURE TEST")
    logger.info("="*70)

    # Initialize database
    logger.info("\n[INIT] Initializing database...")
    init_db()

    # Create sample data
    logger.info("[DATA] Creating sample jobs...")
    db = SessionLocal()

    sample_jobs = [
        {
            "title": "Solidity Developer",
            "company": "Uniswap Labs",
            "location": "Remote",
            "url": "https://example.com/job1",
            "source_site": "web3.career",
            "scraped_at": datetime.utcnow(),
            "coin_ticker": "UNI",
        },
        {
            "title": "Python Backend Engineer",
            "company": "Chainlink Labs",
            "location": "San Francisco",
            "url": "https://example.com/job2",
            "source_site": "cryptojobs.com",
            "scraped_at": datetime.utcnow(),
            "coin_ticker": "LINK",
        },
    ]

    insert_or_update_jobs(sample_jobs, db)
    db.close()

    logger.info("[OK] Sample jobs created")

    # Test formatters
    logger.info("\n[FORMATTERS] Testing message formatters...")

    # Test start message
    start_msg = format_start_message()
    logger.info(f"[OK] Start message: {len(start_msg)} chars")
    assert "Welcome" in start_msg
    assert "/start" in start_msg

    # Test handlers
    logger.info("\n[HANDLERS] Testing command handlers...")

    # Mock update and context
    mock_update = AsyncMock()
    mock_update.effective_user.id = 12345
    mock_update.message.reply_text = AsyncMock()

    # Test /start
    logger.info("[TEST] /start handler...")
    mock_update.message.reply_text.reset_mock()
    await start_handler(mock_update, None)
    assert mock_update.message.reply_text.called
    logger.info("[OK] /start handler works")

    # Test /coin with no args
    logger.info("[TEST] /coin handler (no args)...")
    mock_context = MagicMock()
    mock_context.args = []
    mock_update.message.reply_text.reset_mock()
    await coin_handler(mock_update, mock_context)
    assert mock_update.message.reply_text.called
    logger.info("[OK] /coin handler handles missing args")

    # Test /coin with args
    logger.info("[TEST] /coin handler (with args)...")
    mock_context.args = ["UNI"]
    mock_update.message.reply_text.reset_mock()
    await coin_handler(mock_update, mock_context)
    assert mock_update.message.reply_text.call_count >= 1
    logger.info("[OK] /coin handler works")

    # Test /new
    logger.info("[TEST] /new handler...")
    mock_update.message.reply_text.reset_mock()
    await new_handler(mock_update, mock_context)
    assert mock_update.message.reply_text.called
    logger.info("[OK] /new handler works")

    # Test /expiring
    logger.info("[TEST] /expiring handler...")
    mock_update.message.reply_text.reset_mock()
    await expiring_handler(mock_update, mock_context)
    assert mock_update.message.reply_text.called
    logger.info("[OK] /expiring handler works")

    logger.info("\n" + "="*70)
    logger.info("BOT STRUCTURE TEST COMPLETED")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_bot_structure())
        logger.info("[OK] All tests passed!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)
