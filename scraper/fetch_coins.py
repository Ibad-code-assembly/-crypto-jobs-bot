import httpx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.models import Coin, get_session, init_db

COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"


def fetch_top_coins(limit=100):
    """
    Fetch top 100 coins from CoinGecko API and store in database.
    CoinGecko limits to 250 per request, so we need 1 request for top 100.
    """
    init_db()
    session = get_session()

    try:
        # Fetch in batches of 250 (CoinGecko's max)
        all_coins = []
        for page in range(1, 2):  # Just 1 page needed for top 100
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": page,
                "sparkline": False,
            }

            print(f"Fetching page {page}...")
            response = httpx.get(COINGECKO_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            coins_data = response.json()

            if not coins_data:
                break

            all_coins.extend(coins_data)

            if len(all_coins) >= limit:
                break

        # Trim to exact limit
        all_coins = all_coins[:limit]

        # Insert/update coins in database
        inserted = 0
        updated = 0

        for coin_data in all_coins:
            coin_id = coin_data.get("id")
            symbol = coin_data.get("symbol", "").upper()
            name = coin_data.get("name", "")
            market_cap_rank = coin_data.get("market_cap_rank")

            if not coin_id or not symbol or not name:
                print(f"Skipping incomplete record: {coin_data}")
                continue

            # Check if coin exists
            existing = session.query(Coin).filter(Coin.id == coin_id).first()

            if existing:
                existing.symbol = symbol
                existing.name = name
                existing.market_cap_rank = market_cap_rank
                updated += 1
            else:
                new_coin = Coin(
                    id=coin_id,
                    symbol=symbol,
                    name=name,
                    market_cap_rank=market_cap_rank,
                )
                session.add(new_coin)
                inserted += 1

        session.commit()
        print(f"\n[OK] Successfully processed {len(all_coins)} coins")
        print(f"  Inserted: {inserted}")
        print(f"  Updated: {updated}")

        # Verify a few key coins
        btc = session.query(Coin).filter(Coin.id == "bitcoin").first()
        eth = session.query(Coin).filter(Coin.id == "ethereum").first()
        sol = session.query(Coin).filter(Coin.id == "solana").first()

        print(f"\nVerification:")
        print(f"  BTC: {btc}")
        print(f"  ETH: {eth}")
        print(f"  SOL: {sol}")

        # Count total coins
        total = session.query(Coin).count()
        print(f"\nTotal coins in database: {total}")

    except Exception as e:
        print(f"Error fetching coins: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    fetch_top_coins()
