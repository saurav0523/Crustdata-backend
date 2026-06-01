from sqlalchemy import Column, String, Integer, JSON, DateTime, func, Float
from app.core.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    company_domain = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    snapshot = Column(JSON, nullable=True)          # last known headcount, funding etc.
    added_at = Column(DateTime, server_default=func.now())
    last_checked_at = Column(DateTime, nullable=True)
