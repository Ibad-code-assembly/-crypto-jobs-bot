# Running Everything on Localhost

Quick setup guide to run the full stack locally: Frontend, Backend API, and Telegram Bot.

## Prerequisites

- Python 3.9+ with pip
- Node.js 18+ with npm
- Git (already have this)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                           │
│                 http://localhost:3000                           │
│  • Landing page, dashboard, job listings, coin tracking        │
│  • Calls API at http://localhost:8000/api                      │
└─────────────────────────────────────────────────────────────────┘
                              ↑↓
┌─────────────────────────────────────────────────────────────────┐
│               Backend API (FastAPI)                             │
│                 http://localhost:8000                           │
│  • REST endpoints: /api/jobs, /api/coins, /api/stats, etc.     │
│  • Serves Swagger UI at /docs                                  │
│  • Uses mock data (no database required)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Telegram Bot (Python)                              │
│          (Connects via Telegram API)                            │
│  • Commands: /jobs, /coin BTC, /new, /newlistings, etc.        │
│  • Scrapes job listings and coin exchange data                 │
│  • Sends notifications to groups/users                         │
└─────────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Step 1: Backend API (FastAPI)

**Terminal 1 - Backend:**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the batch file (Windows)
run_api.bat

# Or use the shell script (Unix/Mac)
./run_api.sh
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Watching for file changes in '/path/to/project'
```

**Test it:**
- Open browser: http://localhost:8000
- API Docs: http://localhost:8000/docs (Swagger UI)
- Health check: http://localhost:8000/health

### Step 2: Frontend (Next.js)

**Terminal 2 - Frontend:**

```bash
cd web

# Install Node dependencies (first time only)
npm install

# Run development server
npm run dev

# Or if you prefer production build
npm run build
npm run start
```

**Expected output:**
```
> next dev

  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 2.5s
```

**Test it:**
- Open browser: http://localhost:3000
- You should see the landing page
- Click "Dashboard" to view the dashboard
- All charts should show data from the API

### Step 3: Telegram Bot (Optional)

**Terminal 3 - Bot:**

```bash
# Make sure .env has your BOT_TOKEN
# BOT_TOKEN=your_token_here

python main_integrated.py
```

**Expected output:**
```
======================================================================
CRYPTO JOBS BOT - INTEGRATED (Bot + Scheduler + Notifications)
======================================================================
[INIT] Initializing database...
[OK] Database initialized
[BOT] Creating Telegram application...
[OK] Telegram bot connected and running
```

## Environment Variables

Create/update `.env` file in the root directory:

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_PROXY=http://proxy.example.com:8080  # Optional

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./crypto_jobs.db

# Debug
DEBUG=True
LOG_LEVEL=INFO
```

## Testing the Integration

### 1. Test API Endpoints

```bash
# List jobs
curl http://localhost:8000/api/jobs

# Get dashboard stats
curl http://localhost:8000/api/stats/dashboard

# Get jobs trend chart
curl http://localhost:8000/api/charts/jobs-trend

# Search coins
curl "http://localhost:8000/api/coins?symbol=BTC"
```

### 2. Test Frontend

1. Open http://localhost:3000
2. Navigate to Dashboard
3. Verify charts load data
4. Click through tabs (Overview, Jobs, Coins, Analytics)
5. Try filters (select coins, exchanges, date ranges)

### 3. Test Bot Commands

Send these commands in a Telegram group/chat:

```
/start
/jobs
/coin BTC
/new
/newlistings
/listings30
/subscribe ETH
/mysubs
```

## Troubleshooting

### Frontend can't reach API (CORS error)

**Solution:** Make sure both are running:
- Frontend on http://localhost:3000
- API on http://localhost:8000

CORS is configured in `api/main.py` to allow `localhost:3000`

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ...
]
```

### API won't start (Port 8000 already in use)

```bash
# Find what's using port 8000
lsof -i :8000  # Unix/Mac

netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
python -m uvicorn api.main:app --port 8001
```

Then update frontend env var:
```
# web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001/api
```

### Frontend won't start (Port 3000 already in use)

```bash
# Use different port
npm run dev -- -p 3001
```

### Node modules not installed

```bash
cd web
npm install
```

### Python dependencies missing

```bash
pip install -r requirements.txt --upgrade
```

### Database issues

```bash
# Reset database
rm crypto_jobs.db

# Or in Python shell
from db.database import init_db
init_db()
```

## Performance Tuning

### Frontend Development

- Next.js development mode with hot reload
- Tailwind CSS in development
- Framer Motion animations enabled

```bash
npm run dev
```

### Frontend Production

- Optimized bundle
- Next.js static generation
- CSS minification

```bash
npm run build
npm run start
```

### API Development

- Uvicorn with auto-reload
- Debug logging enabled
- Swagger UI for testing

```bash
python -m uvicorn api.main:app --reload
```

### API Production

- Gunicorn with multiple workers
- Compressed responses
- No reload

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app
```

## File Structure

```
crypto-jobs-bot/
├── web/                          # Next.js frontend
│   ├── src/
│   │   ├── pages/               # Page routes
│   │   │   ├── index.tsx        # Landing page
│   │   │   └── dashboard.tsx    # Dashboard
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks (API calls)
│   │   ├── api/                 # API client
│   │   └── store/               # Zustand state
│   ├── package.json
│   └── tsconfig.json
│
├── api/                          # FastAPI backend
│   ├── main.py                  # App entry point
│   ├── config.py                # Configuration
│   ├── schemas.py               # Pydantic models
│   ├── data.py                  # Mock data
│   └── routes/                  # API endpoints
│       ├── jobs.py
│       ├── coins.py
│       ├── companies.py
│       ├── exchanges.py
│       ├── stats.py
│       └── charts.py
│
├── bot/                         # Telegram bot
│   ├── handlers.py              # Command handlers
│   ├── formatters.py            # Message formatting
│   └── notifications.py         # Notification manager
│
├── db/                          # Database
│   ├── models.py                # SQLAlchemy models
│   ├── queries.py               # Database queries
│   └── database.py              # DB connection
│
├── main_integrated.py           # Bot entry point
├── requirements.txt             # Python dependencies
├── run_api.bat                  # Windows API runner
├── run_api.sh                   # Unix/Mac API runner
└── LOCALHOST_SETUP.md           # This file
```

## Common Commands

### Start Everything

**Terminal 1 (Backend):**
```bash
python -m uvicorn api.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd web && npm run dev
```

**Terminal 3 (Bot - Optional):**
```bash
python main_integrated.py
```

### Stop Everything

```bash
# Ctrl+C in each terminal to gracefully shutdown
Ctrl+C
```

### View Logs

**API:** Terminal 1 shows all Uvicorn logs
**Frontend:** Terminal 2 shows all Next.js logs
**Bot:** Terminal 3 shows all bot activity

## What's Included

### Frontend (Phase 2-3)
- ✅ Landing page with CTAs
- ✅ Professional dashboard
- ✅ Job listings view
- ✅ Coin listings view
- ✅ Analytics tab
- ✅ Advanced filtering

### Backend API (Phase 5)
- ✅ Complete REST API
- ✅ 10+ endpoints
- ✅ Mock data included
- ✅ Swagger UI docs
- ✅ Pagination & filtering

### Telegram Bot
- ✅ Job search commands
- ✅ Coin tracking
- ✅ Notifications
- ✅ Subscriptions
- ✅ New coin listing alerts

## Next Steps

1. **Run locally** following this guide
2. **Explore the dashboard** at http://localhost:3000
3. **Test the API** at http://localhost:8000/docs
4. **Connect your Telegram bot** for notifications
5. **Deploy to production** (Phase 7)

## Production Deployment

See `PHASE_5_COMPLETE.md` and `PHASE_7_DEPLOYMENT.md` for production setup on Railway, Docker, etc.

## Support

For issues:
1. Check logs in the terminal
2. Test endpoints with curl or Postman
3. Check CORS configuration
4. Verify port numbers
5. Check environment variables

Happy coding! 🚀
