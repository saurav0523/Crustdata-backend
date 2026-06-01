from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.schemas import WatchlistItemCreate, WatchlistItemOut
from app.models.watchlist import WatchlistItem
from app.services.apollo import enrich_company
from app.core.database import get_db

router = APIRouter(prefix="/watchlist", tags=["watchlist"])
DEMO_USER = "demo"


@router.get("/", response_model=list[WatchlistItemOut])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == DEMO_USER)
    )
    return result.scalars().all()


@router.post("/", response_model=WatchlistItemOut)
async def add_to_watchlist(body: WatchlistItemCreate, db: AsyncSession = Depends(get_db)):
    # Prevent duplicates
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == DEMO_USER,
            WatchlistItem.company_domain == body.company_domain,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Already in watchlist")

    snapshot = await enrich_company(body.company_domain)
    item = WatchlistItem(
        user_id=DEMO_USER,
        company_domain=body.company_domain,
        company_name=body.company_name,
        snapshot=snapshot,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{item_id}/refresh", response_model=WatchlistItemOut)
async def refresh_watchlist_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == DEMO_USER,
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    fresh = await enrich_company(item.company_domain)
    item.snapshot = fresh
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def remove_from_watchlist(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == DEMO_USER,
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(item)
    await db.commit()
