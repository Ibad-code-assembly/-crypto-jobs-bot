# 🚀 Complete Localhost Setup - 100% Working

**This guide will get everything running on localhost in 5 minutes.**

---

## Prerequisites Check

Make sure you have installed:
- ✅ Python 3.9+ (`python --version`)
- ✅ Node.js 18+ (`node --version`)
- ✅ npm 9+ (`npm --version`)
- ✅ Git (`git --version`)

---

## Step 1: Prepare Environment Files (2 minutes)

### 1.1 Create `.env` file in project root

**Windows (PowerShell):**
```powershell
New-Item -Path .env -Force
```

**Mac/Linux:**
```bash
touch .env
```

### 1.2 Copy this content to `.env`

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_token_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Database
DATABASE_URL=sqlite:///./crypto_jobs.db

# Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Logging
LOG_LEVEL=INFO
```

### 1.3 Create `web/.env.local` file

**Windows (PowerShell):**
```powershell
cd web
New-Item -Path .env.local -Force
```

**Mac/Linux:**
```bash
cd web
touch .env.local
```

### 1.4 Copy this content to `web/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NODE_ENV=development
```

---

## Step 2: Install Dependencies (2 minutes)

### 2.1 Install Python dependencies

**Windows (PowerShell):**
```powershell
# From project root
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
# From project root
pip install -r requirements.txt
```

### 2.2 Install Node dependencies

**Windows (PowerShell):**
```powershell
cd web
npm install
```

**Mac/Linux:**
```bash
cd web
npm install
```

**This may take 1-2 minutes. Wait for it to complete.**

---

## Step 3: Start Services (Open 3 Terminals)

### Terminal 1: FastAPI Backend ⚡

**Windows (PowerShell):**
```powershell
# From project root
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Mac/Linux:**
```bash
# From project root
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Watching for file changes in...
```

✅ **API is ready at http://localhost:8000**

---

### Terminal 2: Next.js Frontend 🌐

**Windows (PowerShell):**
```powershell
# From project root
cd web
npm run dev
```

**Mac/Linux:**
```bash
# From project root
cd web
npm run dev
```

**Expected output:**
```
> next dev
▲ Next.js 14.0.0
- Local:        http://localhost:3000
- Environments: .env.local
✓ Ready in 2.5s
```

✅ **Frontend is ready at http://localhost:3000**

---

### Terminal 3 (Optional): Telegram Bot 🤖

**Windows (PowerShell):**
```powershell
# From project root (only if you have BOT_TOKEN)
python main_integrated.py
```

**Mac/Linux:**
```bash
# From project root (only if you have BOT_TOKEN)
python main_integrated.py
```

**Expected output:**
```
======================================================================
CRYPTO JOBS BOT - INTEGRATED
======================================================================
[INIT] Initializing database...
[OK] Database initialized
```

⚠️ **Note: Skip this if you don't have a Telegram BOT_TOKEN**

---

## Step 4: Verify Everything is Working

### 4.1 Test Backend API

**Open in browser or use curl:**

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Get jobs
curl http://localhost:8000/api/jobs

# Test 3: Get coins
curl http://localhost:8000/api/coins

# Test 4: Dashboard stats
curl http://localhost:8000/api/stats/dashboard
```

**Expected response (JSON):**
```json
{
  "status": "healthy",
  "service": "crypto-jobs-api",
  "version": "1.0.0"
}
```

### 4.2 Test API Swagger Docs

Open in browser:
```
http://localhost:8000/docs
```

You should see interactive Swagger UI with all endpoints.

### 4.3 Test Frontend

Open in browser:
```
http://localhost:3000
```

You should see:
- ✅ Landing page with crypto theme
- ✅ Header with navigation
- ✅ Dashboard link
- ✅ Features, pricing, testimonials

---

## Step 5: Navigate the Application

### 5.1 Homepage
```
http://localhost:3000
```
- See landing page with CTA buttons
- Click "Dashboard" to go to dashboard

### 5.2 Dashboard
```
http://localhost:3000/dashboard
```
- See 4 KPI metrics
- View job trend chart (7 days)
- See exchange breakdown
- Top hiring companies
- Hot coins panel

### 5.3 Jobs Page
```
http://localhost:3000/jobs
```
- Browse all jobs
- Filter by coin
- Pagination
- Apply buttons

### 5.4 Coins Page
```
http://localhost:3000/coins
```
- View all coin listings
- See exchanges per coin
- Filter by trading pairs

### 5.5 Analytics
```
http://localhost:3000/analytics
```
- Deep market insights
- All charts together
- Trend analysis

### 5.6 Settings
```
http://localhost:3000/settings
```
- Theme settings
- Auto refresh toggle
- Notification preferences

### 5.7 API Documentation
```
http://localhost:8000/docs
```
- Interactive Swagger UI
- Test all endpoints
- See request/response examples

---

## Troubleshooting

### Issue: "Port 8000 already in use"

**Solution:**
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Or use different port
python -m uvicorn api.main:app --port 8001
```

Then update `web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001/api
```

### Issue: "Port 3000 already in use"

**Solution:**
```powershell
# Use different port
npm run dev -- -p 3001
```

Then open: http://localhost:3001

### Issue: "Module not found" (Python)

**Solution:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "npm ERR!" during install

**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Remove node_modules
cd web
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Reinstall
npm install
```

### Issue: Frontend shows "Cannot reach API"

**Check:**
1. Is backend running? (Check Terminal 1)
2. Is `.env.local` correct? (Should have `NEXT_PUBLIC_API_URL=http://localhost:8000/api`)
3. Try hard refresh in browser: `Ctrl+Shift+R`

### Issue: "CORS error" in browser console

**Solution:** Already configured in backend. Restart both services.

### Issue: Charts not loading

**Check:**
1. Open browser DevTools (F12)
2. Check Network tab for `/api/charts/...` requests
3. Should return 200 OK with JSON data
4. If 404, backend is not running

---

## Complete Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Landing page & dashboard |
| **API Root** | http://localhost:8000 | API base URL |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **API Health** | http://localhost:8000/health | Health check endpoint |
| **Dashboard** | http://localhost:3000/dashboard | Main dashboard |
| **Jobs** | http://localhost:3000/jobs | Job listings |
| **Coins** | http://localhost:3000/coins | Coin listings |
| **Analytics** | http://localhost:3000/analytics | Analytics page |
| **Settings** | http://localhost:3000/settings | Settings page |

---

## Testing API Endpoints with Examples

### Get All Jobs
```bash
curl "http://localhost:8000/api/jobs?page=1&pageSize=10"
```

### Get Jobs by Coin
```bash
curl "http://localhost:8000/api/jobs?coin=BTC"
```

### Search Jobs
```bash
curl "http://localhost:8000/api/jobs/search?search=engineer"
```

### Get All Coins
```bash
curl "http://localhost:8000/api/coins"
```

### Get Trending Coins
```bash
curl "http://localhost:8000/api/coins/trending"
```

### Get Specific Coin
```bash
curl "http://localhost:8000/api/coins/BTC"
```

### Get Companies
```bash
curl "http://localhost:8000/api/companies/top"
```

### Get Dashboard Stats
```bash
curl "http://localhost:8000/api/stats/dashboard"
```

### Get Health Status
```bash
curl "http://localhost:8000/api/stats/health"
```

### Get Jobs Trend (Chart)
```bash
curl "http://localhost:8000/api/charts/jobs-trend"
```

### Get Exchange Breakdown
```bash
curl "http://localhost:8000/api/charts/exchange-breakdown"
```

---

## Stop Everything

### When Done, Press Ctrl+C in Each Terminal

```
Terminal 1 (API):    Ctrl+C
Terminal 2 (Web):    Ctrl+C
Terminal 3 (Bot):    Ctrl+C
```

**All services will stop gracefully.**

---

## Start Again Next Time

Just run the same 3 terminal commands:

**Terminal 1:**
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2:**
```powershell
cd web && npm run dev
```

**Terminal 3 (optional):**
```powershell
python main_integrated.py
```

---

## Quick Reference Card

### Paths
- **Frontend**: `D:\crypto-jobs-bot\web`
- **Backend**: `D:\crypto-jobs-bot\api`
- **Bot**: `D:\crypto-jobs-bot\main_integrated.py`

### Commands Summary
```powershell
# Terminal 1 - API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd web && npm run dev

# Terminal 3 - Bot (optional)
python main_integrated.py
```

### URLs Summary
```
http://localhost:3000           → Frontend
http://localhost:8000           → API Root
http://localhost:8000/docs      → API Swagger UI
http://localhost:8000/health    → Health Check
```

---

## Common Issues Quick Fix

| Issue | Quick Fix |
|-------|-----------|
| Port in use | Use different port: `--port 8001` |
| Dependencies missing | Run `pip install -r requirements.txt` |
| npm install fails | `npm cache clean --force` then retry |
| API not responding | Check Terminal 1 (API running?) |
| CORS error | Restart both services |
| Charts not loading | Open DevTools (F12) → Network tab |

---

## Success! 🎉

If you can see:
- ✅ Frontend at http://localhost:3000
- ✅ API docs at http://localhost:8000/docs
- ✅ Charts and data on dashboard
- ✅ No errors in terminals

**Then you have a 100% working localhost setup!**

---

## Next: Explore the Application

1. **Landing Page** - See full features and CTAs
2. **Dashboard** - View metrics and charts
3. **Jobs Page** - Browse job listings
4. **Coins Page** - View coin exchange listings
5. **Analytics** - Deep market insights
6. **Settings** - Configure preferences
7. **API Docs** - Test endpoints directly

---

**Happy coding! 🚀**

Questions? Check the logs in each terminal for error messages.
