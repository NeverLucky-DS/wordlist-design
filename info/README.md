# Project map (read this first)

Compact reference for AI/human review. **Start here** instead of scanning the whole repo.

| Doc | Contents |
|-----|----------|
| [architecture.md](architecture.md) | Deploy, nginx, services, data flow |
| [frontend.md](frontend.md) | HTML pages, JS/CSS modules, assets |
| [backend-api.md](backend-api.md) | REST endpoints |
| [pipeline.md](pipeline.md) | Word enrichment pipeline (v2 production path) |
| [data-model.md](data-model.md) | PostgreSQL tables |
| [files.md](files.md) | Canonical file tree (what matters) |
| [known-debt.md](known-debt.md) | Remaining tech debt (short) |
| [AUDIT.md](AUDIT.md) | Full audit report (dated) |

## One-paragraph summary

**Deutsch Essay Trainer** — B1–C1 German essay app. Vanilla HTML/JS frontend (nginx :8753) talks to FastAPI backend (:8000) + PostgreSQL. Users browse a thematic word list (`index.html`), write essays (`editor.html`), plan essays (`schreiben.html`), and ops watch an autonomous word-enrichment pipeline (`pipeline.html`). Backend uses Mistral for essay analysis + word enrichment, Grok/DDG for article discovery.

## Production entry points

| URL | File | Backend |
|-----|------|---------|
| `/` | `index.html` | `GET /api/words` (optional) |
| `/editor.html` | `editor.html` | essays, words, phrases, analyze/stream |
| `/schreiben.html` | `schreiben.html` | none (static demo data) |
| `/pipeline.html` | `pipeline.html` | `/api/pipeline/*` |
| `/api/*` | — | all routes |
| `/health` | — | liveness |

## Do not waste tokens on

- `screenshots/` — README images only
- `backend/scripts/`, `backend/audit_db.py` — manual maintenance CLIs
- `backend/data/` — local SQLite (gitignored)
- `PIPELINE.md` — long design doc; use [pipeline.md](pipeline.md) for current behavior
