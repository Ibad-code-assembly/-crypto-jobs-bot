from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from api.data import COMPANIES_DATA

router = APIRouter()


@router.get("", response_model=dict)
async def list_companies(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    """Get paginated list of all companies."""
    total = len(COMPANIES_DATA)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = COMPANIES_DATA[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "hasMore": end < total,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/top", response_model=dict)
async def top_companies():
    """Get top hiring companies (ranked by job count)."""
    sorted_companies = sorted(COMPANIES_DATA, key=lambda x: x["jobCount"], reverse=True)

    return {
        "data": sorted_companies[:10],
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/{name}", response_model=dict)
async def get_company(name: str):
    """Get details for a specific company by name."""
    company = next(
        (c for c in COMPANIES_DATA if c["name"].lower() == name.lower()),
        None,
    )

    if not company:
        raise HTTPException(status_code=404, detail=f"Company {name} not found")

    return {
        "data": company,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
