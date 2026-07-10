from fastapi import APIRouter
from datetime import datetime
from api.data import EXCHANGES_DATA

router = APIRouter()


@router.get("", response_model=dict)
async def list_exchanges(
    page: int = 1,
    pageSize: int = 20,
):
    """Get paginated list of exchanges."""
    total = len(EXCHANGES_DATA)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = EXCHANGES_DATA[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "hasMore": end < total,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/breakdown", response_model=dict)
async def exchange_breakdown():
    """Get exchange breakdown (coin count per exchange)."""
    breakdown = [
        {
            "id": ex["id"],
            "name": ex["name"],
            "coinCount": ex["coinCount"],
            "jobCount": ex["jobCount"],
        }
        for ex in EXCHANGES_DATA
    ]

    return {
        "data": breakdown,
        "total": len(breakdown),
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
