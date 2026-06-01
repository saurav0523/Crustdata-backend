from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.schemas.schemas import CompanySearchRequest, SavedSearchCreate, SavedSearchOut
from app.services.apollo import enrich_company, search_companies
from app.models.company import SavedSearch
from app.core.database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])

# Hardcoded demo user for now — swap with JWT auth middleware
DEMO_USER = "demo"


@router.get("/enrich")
async def get_company(domain: str):
    """Enrich a single company by domain. Cached in Redis."""
    company = await enrich_company(domain)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/search")
async def search(body: CompanySearchRequest):
    """Search companies with filters. Results cached for 30 min."""
    results = await search_companies(
        query=body.query,
        industry=body.industry,
        min_headcount=body.min_headcount,
        min_funding=body.min_funding,
        hiring_status=body.hiring_status,
        yc_only=body.yc_only,
        offset=body.offset,
        count=body.count,
    )
    return {"results": results, "count": len(results)}


@router.get("/saved-searches", response_model=list[SavedSearchOut])
async def list_saved_searches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SavedSearch).where(SavedSearch.user_id == DEMO_USER)
    )
    return result.scalars().all()


@router.post("/saved-searches", response_model=SavedSearchOut)
async def create_saved_search(body: SavedSearchCreate, db: AsyncSession = Depends(get_db)):
    item = SavedSearch(user_id=DEMO_USER, name=body.name, filters=body.filters)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/saved-searches/{search_id}/run")
async def run_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.user_id == DEMO_USER)
    )
    saved = result.scalars().first()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")

    f = saved.filters
    companies = await search_companies(
        query=f.get("query", ""),
        industry=f.get("industry", ""),
        min_headcount=f.get("min_headcount", 0),
        min_funding=f.get("min_funding", 0),
    )
    await db.execute(
        update(SavedSearch)
        .where(SavedSearch.id == search_id)
        .values(last_run_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"results": companies, "count": len(companies)}


@router.delete("/saved-searches/{search_id}", status_code=204)
async def delete_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.user_id == DEMO_USER)
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(item)
    await db.commit()
