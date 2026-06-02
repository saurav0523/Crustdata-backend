# IntelliScope — Company Intelligence Dashboard

> Built with Crustdata API · FastAPI · React · PostgreSQL · Redis

---

## Architecture

```
React (Vite)
    ↓ REST
FastAPI Gateway  ──→  Crustdata API (proxy + cache)
    ↓                      ↑ httpx
Services Layer             Redis (TTL cache)
    ↓
PostgreSQL
    + APScheduler (alert polling every N minutes)
    + Email / Webhook delivery
```

## Features

| Feature | How |
|---|---|
| Company search | `POST /api/v1/companies/search` → Crustdata `/screener/screen/` |
| Company enrichment | `GET /api/v1/companies/enrich?domain=...` → Crustdata `/screener/company` |
| Redis cache | All Crustdata responses cached (1h enrich, 30min search) |
| Watchlist | Save companies to DB, snapshot stored, refreshable |
| Saved searches | Save filter combos, re-run with one click |
| Alerts | Set headcount/funding/jobs thresholds per company |
| Alert polling | APScheduler polls watched companies every hour |
| Notifications | Email (SMTP) + Webhook delivery on trigger |

---

## Quick Start

### 1. Clone and install

```bash
git clone <repo>
cd intelliscope/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your CRUSTDATA_API_KEY and DATABASE_URL
```

### 3. Start services

```bash
# PostgreSQL + Redis (docker-compose.yml provided)
docker compose up -d

# Run FastAPI
uvicorn app.main:app --reload --port 8080
```

### 4. API docs

Open `http://localhost:8080/docs` — Swagger UI with all endpoints.

---

## API Endpoints

### Companies
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/companies/search` | Search with filters |
| `GET` | `/api/v1/companies/enrich` | Enrich by domain |
| `GET` | `/api/v1/companies/saved-searches` | List saved searches |
| `POST` | `/api/v1/companies/saved-searches` | Create saved search |
| `POST` | `/api/v1/companies/saved-searches/{id}/run` | Re-run search |

### Watchlist
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/watchlist/` | List watchlist |
| `POST` | `/api/v1/watchlist/` | Add company |
| `GET` | `/api/v1/watchlist/{id}/refresh` | Refresh snapshot |
| `DELETE` | `/api/v1/watchlist/{id}` | Remove |

### Alerts
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/alerts/` | List all alerts |
| `POST` | `/api/v1/alerts/` | Create alert |
| `PATCH` | `/api/v1/alerts/{id}/pause` | Pause |
| `PATCH` | `/api/v1/alerts/{id}/resume` | Resume |
| `DELETE` | `/api/v1/alerts/{id}` | Delete |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS
│   ├── core/
│   │   ├── config.py            # pydantic-settings from .env
│   │   ├── database.py          # SQLAlchemy async engine
│   │   └── cache.py             # Redis helpers
│   ├── models/
│   │   ├── company.py           # SavedSearch table
│   │   ├── watchlist.py         # WatchlistItem table
│   │   └── alert.py             # Alert table + enums
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── services/
│   │   ├── crustdata.py         # Crustdata API client + cache layer
│   │   └── alert_poller.py      # APScheduler + email/webhook delivery
│   └── api/routes/
│       ├── companies.py
│       ├── watchlist.py
│       └── alerts.py
└── requirements.txt
```
