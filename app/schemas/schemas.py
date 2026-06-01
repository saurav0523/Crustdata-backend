from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class CompanySearchRequest(BaseModel):
    query: str = ""
    industry: str = ""
    min_headcount: int = 0
    min_funding: float = Field(0, description="In millions USD")
    hiring_status: Optional[str] = "all"
    yc_only: bool = False
    offset: int = 0
    count: int = Field(15, le=100)


class SavedSearchCreate(BaseModel):
    name: str
    filters: dict[str, Any]


class SavedSearchOut(BaseModel):
    id: int
    name: str
    filters: dict[str, Any]
    created_at: datetime
    last_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WatchlistItemCreate(BaseModel):
    company_domain: str
    company_name: str


class WatchlistItemOut(BaseModel):
    id: int
    company_domain: str
    company_name: str
    snapshot: Optional[dict] = None
    added_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    company_domain: str
    company_name: str
    alert_type: str
    threshold: Optional[dict] = None
    notify_email: Optional[str] = None
    notify_webhook: Optional[str] = None


class AlertOut(BaseModel):
    id: int
    company_domain: str
    company_name: str
    alert_type: str
    threshold: Optional[dict] = None
    status: str
    last_triggered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

