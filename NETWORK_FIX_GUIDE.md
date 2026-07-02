# Network Connectivity Fix Guide

## Root Cause Analysis

**Your ISP/Network is BLOCKING Telegram API servers**

### Diagnostic Results:
```
✅ Google HTTPS:     Works  (status 200)
✅ GitHub API:       Works  (status 200)
✅ Telegram DNS:     Resolves correctly to 149.154.166.110
❌ Telegram API:     TIMEOUT - Connection refused
```

**Conclusion:** The network connection is fine for general HTTPS traffic, but specifically Telegram API servers are blocked at the network level (likely your ISP blocking Telegram).

---

## Solution Options (Ranked by Ease)

### ⭐ SOLUTION 1: Use a VPN (EASIEST & RECOMMENDED)

**Steps:**
1. Download and install a VPN service (NordVPN, ExpressVPN, Surfshark, etc.)
2. Connect to any country
3. Run the bot:
   ```bash
   cd D:\crypto-jobs-bot
   python main_integrated.py
   ```

**Why it works:** VPN masks your traffic and routes it through a different IP address, bypassing ISP blocks.

**Time to fix:** ~2 minutes

---

### 💻 SOLUTION 2: Use a Proxy Server (INTERMEDIATE)

If you have access to a proxy server, configure it in your `.env` file:

**Edit `.env` and uncomment:**
```
TELEGRAM_PROXY=http://proxy_server:8080
```

**Proxy format options:**
```
http://proxy_ip:port              # HTTP proxy
https://proxy_ip:port             # HTTPS proxy
socks5://proxy_ip:port            # SOCKS5 proxy
socks5://username:password@ip:port # SOCKS5 with auth
```

**Example:**
```
TELEGRAM_PROXY=socks5://127.0.0.1:1080
```

Then run:
```bash
python main_integrated.py
```

**How to get a proxy:**
- Ask your organization's IT team
- Use a public proxy service (not recommended for security)
- Set up your own proxy server

---

### 🔧 SOLUTION 3: Use Local Telegram Bot API Server (ADVANCED)

If you have Docker and want to run Telegram Bot API locally:

**Steps:**
1. Install Docker Desktop (https://www.docker.com/products/docker-desktop)
2. Run Telegram Bot API server locally:
   ```bash
   docker run -d -p 8081:8081 --name telegram-api tdlib/telegram-bot-api
   ```
3. Configure bot to use local API (advanced - requires code modification)

**Not recommended for beginners.**

---

## Changes Made to Your Codebase

### ✅ What I Fixed (Non-Breaking Changes):

1. **Added Proxy Support to `bot/main.py`**
   - Checks for `TELEGRAM_PROXY` environment variable
   - Falls back to direct connection if not configured
   - No breaking changes to existing functionality

2. **Added Proxy Support to `main_integrated.py`**
   - Same proxy support as above
   - Graceful error handling

3. **Updated `.env` file**
   - Added optional `TELEGRAM_PROXY` configuration line
   - Added instructions for format

### ✅ Your Code is SAFE
- No scrapers modified
- No database changes
- No handlers modified
- All existing features work as before
- Proxy is completely optional

---

## Quick Start

### Using VPN (Recommended):

```bash
# 1. Connect to VPN first
# 2. Then run:
cd D:\crypto-jobs-bot
python main_integrated.py
```

### Using Proxy:

```bash
# 1. Edit .env and set TELEGRAM_PROXY
# 2. Then run:
cd D:\crypto-jobs-bot
python main_integrated.py
```

---

## Testing

After configuring your solution, test with:

```bash
python test_telegram_direct.py
```

Expected output (on success):
```
=== Testing Telegram API Connectivity ===
Attempting to reach api.telegram.org with token...
[OK] Success! Status: 200
Response: {'ok': True, 'result': {'id': 8651166506, ...}}
✓ Telegram API is accessible
```

---

## Troubleshooting

### "Still getting timeout with VPN"
- Try a different VPN server location
- Check if VPN is actually connected
- Restart the bot after connecting to VPN

### "Proxy not working"
- Verify proxy format is correct
- Check if proxy server is accessible
- Test proxy manually: `curl -x [proxy_url] https://api.telegram.org`

### "Bot connects but still slow"
- Normal with VPN/Proxy (adds 100-500ms latency)
- You can optimize by choosing a proxy closer to your location

---

## Summary

| Solution | Effort | Time | Works | Cost |
|----------|--------|------|-------|------|
| VPN | Very Easy | 2 min | ✅ Yes | Paid/Free |
| Proxy | Easy | 5 min | ✅ Yes | Varies |
| Local API | Hard | 30 min | ✅ Yes | Free |

**Recommended:** Use a VPN for simplicity and reliability.

---

Last Updated: 2026-07-02
