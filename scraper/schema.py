from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class Job(BaseModel):
    title: str
    company: str
    location: str
    url: str
    listed_date: Optional[date] = None
    deadline: Optional[date] = None
    source_site: str
    scraped_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Smart Contract Engineer",
                "company": "Uniswap Labs",
                "location": "Remote",
                "url": "https://example.com/job",
                "listed_date": "2026-06-30",
                "deadline": "2026-07-15",
                "source_site": "web3.career",
                "scraped_at": "2026-06-30T12:00:00Z"
            }
        }
