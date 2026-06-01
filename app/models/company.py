# app/models/company.py
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, func
from app.core.database import Base


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    name = Column(String, nullable=False)
    filters = Column(JSON, nullable=False)          # {industry, min_headcount, min_funding, query}
    created_at = Column(DateTime, server_default=func.now())
    last_run_at = Column(DateTime, nullable=True)
