#!/usr/bin/env python3
"""Comprehensive diagnostic test for the bot"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("\n")
print("=" * 70)
print("CRYPTO JOBS BOT - DIAGNOSTIC TEST")
print("=" * 70)
print()

# TEST 1: Check environment variables
print("TEST 1: Checking Environment Variables")
print("-" * 70)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    print("[FAIL] BOT_TOKEN not found in .env")
    sys.exit(1)
else:
    print("[OK] BOT_TOKEN found: %s...***" % BOT_TOKEN[:20])

if not GROUP_CHAT_ID:
    print("[WARN] GROUP_CHAT_ID not found in .env")
else:
    print("[OK] GROUP_CHAT_ID found: %s" % GROUP_CHAT_ID)

if not DATABASE_URL:
    print("[WARN] DATABASE_URL not found in .env")
else:
    print("[OK] DATABASE_URL found: %s" % DATABASE_URL)

print()

# TEST 2: Test Telegram connectivity
print("TEST 2: Testing Telegram Connectivity")
print("-" * 70)

async def test_telegram():
    try:
        bot = Bot(BOT_TOKEN)
        me = await bot.get_me()
        print("[OK] Bot connected to Telegram!")
        print("     Bot name: @%s" % me.username)
        print("     Bot ID: %s" % me.id)
        return True
    except TelegramError as e:
        print("[FAIL] Telegram connection failed: %s" % str(e)[:100])
        return False
    except Exception as e:
        print("[FAIL] Unexpected error: %s" % str(e)[:100])
        return False

try:
    telegram_ok = asyncio.run(test_telegram())
except Exception as e:
    print("[FAIL] Error running async test: %s" % str(e))
    telegram_ok = False

print()

# TEST 3: Check database connectivity
print("TEST 3: Checking Database")
print("-" * 70)

try:
    from db.database import SessionLocal, init_db
    from db.models import Job

    # Try to initialize database
    init_db()
    print("[OK] Database initialized successfully")

    # Try to open a session
    db = SessionLocal()
    db.close()
    print("[OK] Database session works")

    # Count jobs in database
    db = SessionLocal()
    job_count = db.query(Job).count()
    db.close()
    print("[OK] Database has %d jobs" % job_count)

except Exception as e:
    print("[FAIL] Database error: %s" % str(e)[:100])

print()

# TEST 4: Check handlers import
print("TEST 4: Checking Bot Handlers")
print("-" * 70)

try:
    from bot.handlers import (
        start_handler,
        coin_handler,
        new_handler,
        expiring_handler,
        message_handler,
        error_handler,
    )
    print("[OK] All handlers imported successfully")

    # Check if handlers are callable
    if asyncio.iscoroutinefunction(start_handler):
        print("[OK] start_handler is async")
    if asyncio.iscoroutinefunction(message_handler):
        print("[OK] message_handler is async")
    if asyncio.iscoroutinefunction(error_handler):
        print("[OK] error_handler is async")

except Exception as e:
    print("[FAIL] Handler import error: %s" % str(e)[:100])

print()

# TEST 5: Summary
print("=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print()

if telegram_ok:
    print("[OK] Bot can connect to Telegram - you can proceed!")
    print()
    print("Next steps:")
    print("1. Run: python test_bot.py")
    print("2. Send 'hi' in your Telegram group")
    print("3. Bot should reply with a greeting")
    print()
else:
    print("[FAIL] Bot CANNOT connect to Telegram")
    print()
    print("Troubleshooting steps:")
    print("1. Check Windows Firewall:")
    print("   - Run PowerShell as Administrator")
    print("   - Allow port 443 outbound to Telegram")
    print()
    print("2. Check if on corporate network:")
    print("   - Run: netsh winhttp show proxy")
    print("   - Check if proxy is blocking Telegram")
    print()
    print("3. Try disabling firewall temporarily:")
    print("   - Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $false")
    print("   - Run this test again")
    print("   - Then re-enable: Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $true")
    print()

print()
