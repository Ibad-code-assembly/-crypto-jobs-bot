import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_telegram():
    print("=== Testing Telegram API Connectivity ===\n")

    bot_token = os.getenv("BOT_TOKEN")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            print(f"Attempting to reach api.telegram.org with token...")
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = await client.get(url)
            print(f"[OK] Success! Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return True
    except httpx.TimeoutException as e:
        print(f"[TIMEOUT] Connection timed out after 10 seconds")
        print(f"Details: {e}")
        return False
    except httpx.ConnectError as e:
        print(f"[CONNECTION ERROR] Cannot connect to Telegram API")
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram())
    if result:
        print("\n✓ Telegram API is accessible")
    else:
        print("\n✗ Telegram API is NOT accessible - likely ISP/Network block")
