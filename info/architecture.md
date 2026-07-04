# Architecture

## Deploy (`docker-compose.yml`)

```
┌─────────────┐     /api/*, /health     ┌──────────────┐
│ nginx :8753 │ ───────────────────────►│ FastAPI :8000│
│  (frontend) │                         │   backend    │
└─────────────┘                         └──────┬───────┘
      │ mounts: html, css, js,                  │
      │ images/, worte/                          ▼
      │                                   ┌──────────────┐
      └─ static only                      │ PostgreSQL   │
                                          └──────────────┘
```

| Service | Image / build | Ports | Volumes |
|---------|---------------|-------|---------|
| `frontend` | nginx:alpine | 8753→80 | `nginx.conf` + **whole project dir** `.:/usr/share/nginx/html:ro` (dev — avoids stale inode on file replace) |
| `backend` | `Dockerfile` | 8000 | — |
| `postgres` | postgres:16-alpine | internal | `pg_data` |

## Request flow

1. Browser loads static HTML from nginx.
2. JS calls `/api/...` — nginx proxies to `backend:8000` ([`nginx.conf`](../nginx.conf)).
3. [`js/editor-api.js`](../js/editor-api.js) wraps fetch for editor; [`pipeline.html`](../pipeline.html) uses inline fetch.

## Backend layout ([`backend/app/`](../backend/app/))

| Package | Role |
|---------|------|
| `main.py` | FastAPI app, CORS, startup schema + cleanup, scheduler |
| `config.py` | `Settings` from env (`PIPELINE_*`, API keys) |
| `schemas.py` | Pydantic DTOs for API |
| `api/routes/` | HTTP handlers |
| `services/` | DB repos + Mistral analyzer + Wiktionary client + topic packs |
| `db/` | SQLAlchemy models, async session, seed data |
| `pipeline/` | Autonomous word enrichment (see [pipeline.md](pipeline.md)) |

## Startup sequence ([`main.py`](../backend/app/main.py))

1. `create_all` + ad-hoc `ALTER` for new columns
2. `ensure_seed_data`
3. Idempotent cleanup: fix lemmas, dedupe words, normalize topic case
4. If `pipeline_autorun=true` → start background scheduler

## External APIs

| Provider | Used for | Module |
|----------|----------|--------|
| Mistral | Essay analysis, word enrichment, supplement, topic generation | `mistral_analyzer.py`, `pipeline/mistral_http.py` |
| Grok (xAI) | Article URL discovery | `pipeline/discovery.py` |
| DuckDuckGo | Fallback discovery | `pipeline/discovery.py` |
| Wiktionary | Grammar verification / enrichment | `pipeline/enrichment.py`, `services/wiktionary_client.py` |
| DWDS | German dictionary fallback | `pipeline/enrichment.py` |

## Env vars (key)

See [`backend/app/config.py`](../backend/app/config.py). Minimum for full stack:

- `MISTRAL_API_KEY` — essays + pipeline
- `GROK_API_KEY` — discovery
- `DATABASE_URL` — set by compose for Postgres
