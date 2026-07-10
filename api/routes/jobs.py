from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
from api.schemas import JobSchema
from api.data import JOBS_DATA

router = APIRouter()


@router.get("", response_model=dict)
async def list_jobs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    coin: Optional[str] = None,
    company: Optional[str] = None,
):
    """Get paginated list of jobs with optional filters."""
    filtered_jobs = JOBS_DATA

    if coin:
        filtered_jobs = [j for j in filtered_jobs if j["coin"].upper() == coin.upper()]
    if company:
        filtered_jobs = [j for j in filtered_jobs if j["company"].lower() == company.lower()]

    total = len(filtered_jobs)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = filtered_jobs[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "hasMore": end < total,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/search", response_model=dict)
async def search_jobs(
    search: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    """Search jobs by title, company, or location."""
    search_lower = search.lower()
    filtered_jobs = [
        j for j in JOBS_DATA
        if search_lower in j["title"].lower()
        or search_lower in j["company"].lower()
        or search_lower in j["location"].lower()
    ]

    total = len(filtered_jobs)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = filtered_jobs[start:end]

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
async def trending_jobs():
    """Get trending job postings (most recent)."""
    # Sort by recency (assume first items are most recent)
    trending = sorted(JOBS_DATA, key=lambda x: JOBS_DATA.index(x), reverse=True)[:10]

    return {
        "data": trending,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/company/{company}", response_model=dict)
async def jobs_by_company(company: str):
    """Get all jobs for a specific company."""
    jobs = [j for j in JOBS_DATA if j["company"].lower() == company.lower()]

    if not jobs:
        raise HTTPException(status_code=404, detail=f"No jobs found for {company}")

    return {
        "data": jobs,
        "total": len(jobs),
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
