from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, func, Enum
from app.core.database import Base
import enum


class AlertType(str, enum.Enum):
    HEADCOUNT_GROWTH = "headcount_growth"
    FUNDING_RAISED = "funding_raised"
    NEW_JOB_OPENINGS = "new_job_openings"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    company_domain = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    threshold = Column(JSON, nullable=True)         # e.g. {"min_growth_pct": 10}
    notify_email = Column(String, nullable=True)
    notify_webhook = Column(String, nullable=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
