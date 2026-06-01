from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.schemas.schemas import AlertCreate, AlertOut
from app.models.alert import Alert, AlertStatus
from app.core.database import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])
DEMO_USER = "demo"


@router.get("/", response_model=list[AlertOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.user_id == DEMO_USER))
    return result.scalars().all()


@router.post("/", response_model=AlertOut)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = Alert(
        user_id=DEMO_USER,
        company_domain=body.company_domain,
        company_name=body.company_name,
        alert_type=body.alert_type,
        threshold=body.threshold,
        notify_email=body.notify_email,
        notify_webhook=body.notify_webhook,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}/pause", response_model=AlertOut)
async def pause_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == DEMO_USER)
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.PAUSED
    await db.commit()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}/resume", response_model=AlertOut)
async def resume_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == DEMO_USER)
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.ACTIVE
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == DEMO_USER)
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
