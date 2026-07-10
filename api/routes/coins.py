from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from api.data import COINS_DATA, get_trending_coins

router = APIRouter()


@router.get("", response_model=dict)
async def list_coins(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    symbol: Optional[str] = None,
):
    """Get paginated list of coins with optional symbol filter."""
    filtered_coins = COINS_DATA

    if symbol:
        filtered_coins = [c for c in filtered_coins if c["symbol"].upper() == symbol.upper()]

    total = len(filtered_coins)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = filtered_coins[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "hasMore": end < total,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/trending", response_model=dict)
async def trending_coins():
    """Get trending coins (4+ job postings)."""
    trending = get_trending_coins()

    return {
        "data": trending,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/{symbol}", response_model=dict)
async def get_coin(symbol: str):
    """Get details for a specific coin by symbol."""
    coin = next(
        (c for c in COINS_DATA if c["symbol"].upper() == symbol.upper()),
        None,
    )

    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {symbol} not found")

    return {
        "data": coin,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
