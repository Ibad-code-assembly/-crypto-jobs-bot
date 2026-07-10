from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobSchema(BaseModel):
    id: str
    title: str
    company: str
    coin: str
    location: str
    listedDate: str
    source: List[str]
    url: str
    salary: Optional[str] = None
    level: Optional[str] = None

    class Config:
        from_attributes = True


class CoinSchema(BaseModel):
    id: str
    symbol: str
    name: str
    exchanges: List[dict]
    pairs: List[str]
    trendingUp: Optional[bool] = False
    jobCount: int
    lastUpdated: str

    class Config:
        from_attributes = True


class ExchangeSchema(BaseModel):
    id: str
    name: str
    coinCount: int
    jobCount: int

    class Config:
        from_attributes = True


class CompanySchema(BaseModel):
    rank: int
    name: str
    jobCount: int
    recentHires: int

    class Config:
        from_attributes = True


class MetricSchema(BaseModel):
    label: str
    value: int
    trend: dict
    icon: str
    color: str

    class Config:
        from_attributes = True


class HealthStatusSchema(BaseModel):
    label: str
    status: str  # 'online' | 'offline' | 'degraded'
    value: str | int
    icon: str

    class Config:
        from_attributes = True


class JobsTrendDataSchema(BaseModel):
    date: str
    BTC: int
    ETH: int
    SOL: int
    ADA: int

    class Config:
        from_attributes = True


class DashboardStatsSchema(BaseModel):
    totalJobs: int
    activeCompanies: int
    coinsCovered: int
    exchanges: int

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    data: List[BaseModel]
    total: int
    page: int
    pageSize: int
    hasMore: bool


class ApiResponse(BaseModel):
    data: Optional[BaseModel | List[BaseModel]] = None
    timestamp: str
    status: str  # 'success' | 'error'
    message: Optional[str] = None


# Query parameter models
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=20, ge=1, le=100)


class JobFilterParams(PaginationParams):
    coin: Optional[str] = None
    company: Optional[str] = None
    search: Optional[str] = None


class CoinFilterParams(PaginationParams):
    symbol: Optional[str] = None
