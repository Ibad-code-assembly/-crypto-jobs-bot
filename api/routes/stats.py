from fastapi import APIRouter
from datetime import datetime
from api.data import get_dashboard_stats, get_health_status

router = APIRouter()


@router.get("/dashboard", response_model=dict)
async def dashboard_stats():
    """Get dashboard statistics (KPI metrics)."""
    stats = get_dashboard_stats()

    return {
        "data": stats,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/jobs", response_model=dict)
async def jobs_stats():
    """Get job-specific statistics."""
    stats = get_dashboard_stats()

    return {
        "data": {
            "totalJobs": stats["totalJobs"],
            "activeCompanies": stats["activeCompanies"],
            "newJobsToday": 45,
            "newJobsWeek": 312,
            "averagePostingTime": "2.5 days",
        },
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


@router.get("/health", response_model=dict)
async def health_status():
    """Get system health status."""
    health = get_health_status()

    return {
        "data": health,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }
