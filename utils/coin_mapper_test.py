import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.coin_mapper import match_company_to_coin, get_unmatched_companies, clear_unmatched_log

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_coin_mapper():
    """Test coin mapping with various company names."""
    logger.info("\n" + "="*70)
    logger.info("COIN MAPPER TEST")
    logger.info("="*70)

    # Clear previous log
    clear_unmatched_log()

    test_cases = [
        ("Chainlink Labs", "LINK", "manual alias"),
        ("Uniswap Labs", "UNI", "manual alias"),
        ("MakerDAO", "MKR", "manual alias"),
        ("Aave", "AAVE", "manual alias"),
        ("Curve", "CRV", "manual alias"),
        ("Yearn Finance", "YFI", "manual alias"),
        ("Lido", "LDO", "manual alias"),
        ("Compound", "COMP", "manual alias"),
        ("Ethereum Foundation", "ETH", "manual alias"),
        ("Bitcoin Core", "BTC", "manual alias"),
        ("Chainlink", "LINK", "fuzzy match (name)"),
        ("Uniswap", "UNI", "fuzzy match (name)"),
        ("Maker", None, "partial fuzzy - should not match"),
        ("Some Random Company XYZ", None, "should not match"),
        ("Solana", "SOL", "manual alias"),
    ]

    passed = 0
    failed = 0

    logger.info("\n[Testing Company Matching]")
    logger.info("-" * 70)

    for company, expected, description in test_cases:
        result = match_company_to_coin(company)

        if result == expected:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        logger.info(f"{status} {company:<30} -> {result if result else 'None':<6} ({description})")
        if result != expected:
            logger.info(f"       Expected: {expected}, Got: {result}")

    logger.info("-" * 70)

    # Check unmatched log
    unmatched = get_unmatched_companies()
    logger.info(f"\n[Unmatched Companies Log]")
    logger.info(f"Total unmatched entries: {len(unmatched)}")
    if unmatched:
        logger.info("Sample entries:")
        for entry in unmatched[:5]:
            logger.info(f"  {entry}")

    logger.info("\n" + "="*70)
    logger.info(f"TEST RESULTS: {passed} passed, {failed} failed")
    logger.info("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = test_coin_mapper()
    sys.exit(0 if success else 1)
