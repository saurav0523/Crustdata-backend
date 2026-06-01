from typing import Optional
import smtplib
import httpx
from email.mime.text import MIMEText
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.alert import Alert, AlertStatus, AlertType
from app.models.watchlist import WatchlistItem
from app.services.apollo import enrich_company

settings = get_settings()
scheduler = AsyncIOScheduler()


# ── Alert evaluation ────────────────────────────────────────────────────────

def _check_headcount_growth(company: dict, threshold: Optional[dict]) -> bool:
    growth = company.get("headcount", {}).get("six_months_growth_headcount", 0) or 0
    min_pct = (threshold or {}).get("min_growth_pct", 10) / 100
    return growth >= min_pct


def _check_funding(company: dict, snapshot: Optional[dict]) -> bool:
    current = company.get("total_investment_usd") or 0
    previous = (snapshot or {}).get("total_investment_usd") or 0
    return current > previous


def _check_jobs(company: dict, threshold: Optional[dict]) -> bool:
    jobs = company.get("job_openings") or []
    min_jobs = (threshold or {}).get("min_openings", 5)
    return len(jobs) >= min_jobs


EVALUATORS = {
    AlertType.HEADCOUNT_GROWTH: _check_headcount_growth,
    AlertType.FUNDING_RAISED: _check_funding,
    AlertType.NEW_JOB_OPENINGS: _check_jobs,
}


# ── Notification delivery ────────────────────────────────────────────────────

async def _send_email(to: str, company_name: str, alert_type: str):
    if not settings.smtp_host or not to:
        return
    msg = MIMEText(
        f"Signal detected for {company_name}:\n\n"
        f"Alert type: {alert_type}\n\n"
        f"Log in to IntelliScope to view the full company profile."
    )
    msg["Subject"] = f"[IntelliScope] Alert triggered — {company_name}"
    msg["From"] = settings.smtp_user
    msg["To"] = to
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
    except Exception as exc:
        print(f"Email send failed: {exc}")


async def _send_webhook(url: str, payload: dict):
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception as exc:
        print(f"Webhook delivery failed: {exc}")


# ── Core polling job ─────────────────────────────────────────────────────────

async def poll_alerts():
    """Called by APScheduler on the configured interval."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Polling alerts…")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        )
        alerts: list[Alert] = result.scalars().all()

        # Group by domain to avoid duplicate API calls
        domains: dict[str, list[Alert]] = {}
        for alert in alerts:
            domains.setdefault(alert.company_domain, []).append(alert)

        for domain, domain_alerts in domains.items():
            try:
                company = await enrich_company(domain)
            except Exception as exc:
                print(f"Enrich failed for {domain}: {exc}")
                continue
            if not company:
                continue

            snapshot = await _get_snapshot(db, domain)
            for alert in domain_alerts:
                evaluator = EVALUATORS.get(alert.alert_type)
                if not evaluator:
                    continue
                triggered = evaluator(company, alert.threshold or snapshot)
                if triggered:
                    await _fire_alert(db, alert, company)

            await _update_snapshot(db, domain, company)

    print("Poll complete.")


async def _get_snapshot(db: AsyncSession, domain: str) -> Optional[dict]:
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.company_domain == domain)
    )
    item = result.scalars().first()
    return item.snapshot if item else None


async def _update_snapshot(db: AsyncSession, domain: str, company: dict):
    await db.execute(
        update(WatchlistItem)
        .where(WatchlistItem.company_domain == domain)
        .values(snapshot=company, last_checked_at=datetime.now(timezone.utc))
    )
    await db.commit()


async def _fire_alert(db: AsyncSession, alert: Alert, company: dict):
    print(f"  TRIGGERED: {alert.alert_type} for {alert.company_name}")
    await _send_email(alert.notify_email, alert.company_name, alert.alert_type)
    await _send_webhook(alert.notify_webhook, {
        "company": alert.company_name,
        "domain": alert.company_domain,
        "alert_type": alert.alert_type,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": company,
    })
    await db.execute(
        update(Alert)
        .where(Alert.id == alert.id)
        .values(last_triggered_at=datetime.now(timezone.utc), status=AlertStatus.TRIGGERED)
    )
    await db.commit()


def start_scheduler():
    scheduler.add_job(
        poll_alerts,
        "interval",
        minutes=settings.alert_poll_interval_minutes,
        id="alert_poll",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
