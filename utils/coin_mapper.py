import logging
import sys
from pathlib import Path
from datetime import datetime
from rapidfuzz import fuzz

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import SessionLocal
from db.models import Coin
from utils.coin_aliases import COIN_ALIASES

logger = logging.getLogger(__name__)

# Setup unmatched log file
UNMATCHED_LOG_FILE = Path(__file__).parent / "unmatched_companies.log"


def match_company_to_coin(company_name: str) -> str:
    """
    Match company name to coin ticker using:
    1. Manual aliases (COIN_ALIASES)
    2. Fuzzy matching against coin names and symbols (threshold: 80)

    Returns ticker (uppercase) or None if no match found.
    """
    if not company_name:
        return None

    company_clean = company_name.strip()

    # Step 1: Check manual aliases
    if company_clean in COIN_ALIASES:
        ticker = COIN_ALIASES[company_clean]
        logger.debug(f"[ALIAS] {company_clean} -> {ticker}")
        return ticker

    # Step 2: Query coins and fuzzy match
    db = SessionLocal()
    try:
        coins = db.query(Coin).all()

        best_match = None
        best_score = 0

        for coin in coins:
            # Match against coin symbol
            symbol_score = fuzz.token_set_ratio(
                company_clean.upper(),
                coin.symbol.upper()
            )

            # Match against coin name
            name_score = fuzz.token_set_ratio(
                company_clean.lower(),
                coin.name.lower()
            )

            current_best = max(symbol_score, name_score)

            if current_best > best_score:
                best_score = current_best
                best_match = coin.symbol

        db.close()

        # Step 3: Check threshold
        if best_score >= 80:
            logger.debug(f"[FUZZY] {company_clean} -> {best_match} (score: {best_score})")
            return best_match
        else:
            # Log unmatched company
            _log_unmatched(company_clean, best_match, best_score)
            logger.warning(f"[UNMATCHED] {company_clean} (best: {best_match}={best_score})")
            return None

    except Exception as e:
        logger.error(f"Error matching company '{company_name}': {str(e)}")
        db.close()
        return None


def _log_unmatched(company_name: str, best_match: str, score: int):
    """Log unmatched company to file."""
    try:
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = f"{company_name} | {best_match} | {score} | {timestamp}\n"

        with open(UNMATCHED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Error writing to unmatched log: {str(e)}")


def get_unmatched_companies():
    """Read unmatched companies from log file."""
    if not UNMATCHED_LOG_FILE.exists():
        return []

    try:
        with open(UNMATCHED_LOG_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        logger.error(f"Error reading unmatched log: {str(e)}")
        return []


def clear_unmatched_log():
    """Clear the unmatched companies log file."""
    try:
        if UNMATCHED_LOG_FILE.exists():
            UNMATCHED_LOG_FILE.unlink()
            logger.info("Cleared unmatched companies log")
    except Exception as e:
        logger.error(f"Error clearing unmatched log: {str(e)}")
