from datetime import datetime, timedelta
from typing import List, Dict
from api.schemas import (
    JobSchema,
    CoinSchema,
    CompanySchema,
    ExchangeSchema,
    JobsTrendDataSchema,
)

# Mock Jobs Data
JOBS_DATA = [
    {
        "id": "job-1",
        "title": "Senior Blockchain Developer",
        "company": "Coinbase",
        "coin": "BTC",
        "location": "San Francisco, CA",
        "listedDate": "Today",
        "source": ["LinkedIn", "Job Board"],
        "url": "https://coinbase.com/careers",
        "salary": "$150K-$200K",
        "level": "senior",
    },
    {
        "id": "job-2",
        "title": "Smart Contract Engineer",
        "company": "Polygon",
        "coin": "MATIC",
        "location": "Remote",
        "listedDate": "Yesterday",
        "source": ["GitHub"],
        "url": "https://polygon.technology/careers",
        "salary": "$120K-$180K",
        "level": "mid",
    },
    {
        "id": "job-3",
        "title": "DevOps Engineer",
        "company": "Ripple",
        "coin": "XRP",
        "location": "San Francisco, CA",
        "listedDate": "2 days ago",
        "source": ["LinkedIn", "AngelList"],
        "url": "https://ripple.com/careers",
        "salary": "$130K-$170K",
        "level": "mid",
    },
    {
        "id": "job-4",
        "title": "Product Manager",
        "company": "Kraken",
        "coin": "ETH",
        "location": "San Francisco, CA",
        "listedDate": "3 days ago",
        "source": ["Job Board"],
        "url": "https://kraken.com/careers",
        "salary": "$140K-$190K",
        "level": "senior",
    },
    {
        "id": "job-5",
        "title": "Backend Engineer",
        "company": "Gemini",
        "coin": "BTC",
        "location": "New York, NY",
        "listedDate": "Today",
        "source": ["LinkedIn"],
        "url": "https://gemini.com/careers",
        "salary": "$110K-$160K",
        "level": "mid",
    },
    {
        "id": "job-6",
        "title": "Frontend Developer",
        "company": "Coinbase",
        "coin": "ETH",
        "location": "Remote",
        "listedDate": "1 day ago",
        "source": ["GitHub", "LinkedIn"],
        "url": "https://coinbase.com/careers",
        "salary": "$100K-$150K",
        "level": "junior",
    },
    {
        "id": "job-7",
        "title": "Security Researcher",
        "company": "Curve Finance",
        "coin": "CRV",
        "location": "Remote",
        "listedDate": "Today",
        "source": ["Job Board"],
        "url": "https://curve.fi/careers",
        "salary": "$130K-$200K",
        "level": "senior",
    },
    {
        "id": "job-8",
        "title": "Data Analyst",
        "company": "Uniswap",
        "coin": "UNI",
        "location": "San Francisco, CA",
        "listedDate": "2 days ago",
        "source": ["LinkedIn"],
        "url": "https://uniswap.org/careers",
        "salary": "$90K-$140K",
        "level": "mid",
    },
]

# Mock Coins Data
COINS_DATA = [
    {
        "id": "coin-btc",
        "symbol": "BTC",
        "name": "Bitcoin",
        "exchanges": [
            {"name": "Binance", "date": "Today"},
            {"name": "Coinbase", "date": "2 days ago"},
        ],
        "pairs": ["USDT", "USDC", "EUR"],
        "trendingUp": True,
        "jobCount": 145,
        "lastUpdated": datetime.now().isoformat(),
    },
    {
        "id": "coin-eth",
        "symbol": "ETH",
        "name": "Ethereum",
        "exchanges": [
            {"name": "Kraken", "date": "Today"},
            {"name": "OKX", "date": "Yesterday"},
        ],
        "pairs": ["USDT", "USDC", "BTC"],
        "trendingUp": True,
        "jobCount": 128,
        "lastUpdated": datetime.now().isoformat(),
    },
    {
        "id": "coin-sol",
        "symbol": "SOL",
        "name": "Solana",
        "exchanges": [
            {"name": "Bybit", "date": "2 days ago"},
            {"name": "KuCoin", "date": "3 days ago"},
        ],
        "pairs": ["USDT", "USDC"],
        "trendingUp": False,
        "jobCount": 87,
        "lastUpdated": datetime.now().isoformat(),
    },
    {
        "id": "coin-ada",
        "symbol": "ADA",
        "name": "Cardano",
        "exchanges": [
            {"name": "Gate.io", "date": "Today"},
            {"name": "MEXC", "date": "5 days ago"},
        ],
        "pairs": ["USDT", "EUR"],
        "trendingUp": True,
        "jobCount": 65,
        "lastUpdated": datetime.now().isoformat(),
    },
    {
        "id": "coin-xrp",
        "symbol": "XRP",
        "name": "Ripple",
        "exchanges": [
            {"name": "Binance", "date": "Today"},
            {"name": "Kraken", "date": "1 day ago"},
        ],
        "pairs": ["USDT", "USDC"],
        "trendingUp": False,
        "jobCount": 76,
        "lastUpdated": datetime.now().isoformat(),
    },
]

# Mock Companies Data
COMPANIES_DATA = [
    {"rank": 1, "name": "Coinbase", "jobCount": 145, "recentHires": 32},
    {"rank": 2, "name": "Ripple", "jobCount": 98, "recentHires": 21},
    {"rank": 3, "name": "Gemini", "jobCount": 87, "recentHires": 18},
    {"rank": 4, "name": "Kraken", "jobCount": 76, "recentHires": 15},
    {"rank": 5, "name": "Polygon", "jobCount": 65, "recentHires": 12},
]

# Mock Exchanges Data
EXCHANGES_DATA = [
    {"id": "ex-1", "name": "Binance", "coinCount": 2500, "jobCount": 450},
    {"id": "ex-2", "name": "Coinbase", "coinCount": 1250, "jobCount": 320},
    {"id": "ex-3", "name": "Kraken", "coinCount": 980, "jobCount": 280},
    {"id": "ex-4", "name": "OKX", "coinCount": 1480, "jobCount": 290},
    {"id": "ex-5", "name": "Bybit", "coinCount": 1120, "jobCount": 210},
    {"id": "ex-6", "name": "KuCoin", "coinCount": 890, "jobCount": 180},
    {"id": "ex-7", "name": "Gate.io", "coinCount": 1045, "jobCount": 200},
    {"id": "ex-8", "name": "MEXC", "coinCount": 750, "jobCount": 150},
    {"id": "ex-9", "name": "Bitget", "coinCount": 670, "jobCount": 120},
    {"id": "ex-10", "name": "HTX", "coinCount": 580, "jobCount": 95},
]

# Mock 7-day Jobs Trend
def get_jobs_trend() -> List[Dict]:
    today = datetime.now()
    data = []
    for i in range(7):
        date = (today - timedelta(days=6 - i)).strftime("%b %d")
        data.append({
            "date": date,
            "BTC": 40 + i * 3,
            "ETH": 35 + i * 2,
            "SOL": 22 + i * 1,
            "ADA": 18 + i * 1,
        })
    return data


def get_trending_coins() -> List[Dict]:
    """Coins with 4+ job postings"""
    return [
        {"symbol": "BTC", "jobCount": 45, "date": "Today"},
        {"symbol": "ETH", "jobCount": 40, "date": "Today"},
        {"symbol": "SOL", "jobCount": 28, "date": "Today"},
        {"symbol": "XRP", "jobCount": 18, "date": "Yesterday"},
        {"symbol": "ADA", "jobCount": 20, "date": "2 days ago"},
    ]


def get_dashboard_stats() -> Dict:
    return {
        "totalJobs": 10265,
        "activeCompanies": 847,
        "coinsCovered": 1250,
        "exchanges": 38,
    }


def get_health_status() -> List[Dict]:
    return [
        {
            "label": "Scrapers",
            "status": "online",
            "value": "11/11",
            "icon": "⚡",
        },
        {
            "label": "Exchanges",
            "status": "online",
            "value": "10/10",
            "icon": "🏪",
        },
        {
            "label": "Latency",
            "status": "online",
            "value": "234ms",
            "icon": "🕐",
        },
        {
            "label": "Uptime",
            "status": "online",
            "value": "99.8%",
            "icon": "📊",
        },
    ]
