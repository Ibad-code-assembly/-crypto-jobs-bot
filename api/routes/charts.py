from fastapi import APIRouter
from datetime import datetime
from api.data import get_jobs_trend, EXCHANGES_DATA

router = APIRouter()


@router.get("/jobs-trend", response_model=dict)
async def jobs_trend():
    """Get 7-day jobs trend data (BTC, ETH, SOL, ADA)."""
    data = get_jobs_trend()

    return {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/exchange-breakdown", response_model=dict)
async def exchange_breakdown():
    """Get exchange breakdown chart data."""
    data = [
        {
            "id": ex["id"],
            "name": ex["name"],
            "coinCount": ex["coinCount"],
            "percentage": round((ex["coinCount"] / sum(e["coinCount"] for e in EXCHANGES_DATA)) * 100, 1),
        }
        for ex in EXCHANGES_DATA
    ]

    return {
        "data": data,
        "total": len(data),
        "totalCoins": sum(ex["coinCount"] for ex in EXCHANGES_DATA),
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
