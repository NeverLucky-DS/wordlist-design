# Project map (read this first)

Compact reference for AI/human review. **Start here** instead of scanning the whole repo.

| Doc | Contents |
|-----|----------|
| [CRITICAL-LINKS.md](CRITICAL-LINKS.md) | **Safe-delete map — read before refactoring** |
| [architecture.md](architecture.md) | Deploy, nginx, services, data flow |
| [frontend.md](frontend.md) | HTML pages, JS/CSS modules, assets |
| [backend-api.md](backend-api.md) | REST endpoints |
| [pipeline.md](pipeline.md) | Word enrichment pipeline (v2 production path) |
| [data-model.md](data-model.md) | PostgreSQL tables |
| [files.md](files.md) | Canonical file tree (what matters) |
| [known-debt.md](known-debt.md) | Remaining tech debt (short) |
| [graph.md](graph.md) | Code graph (Graphify) — how to navigate the repo structurally |
| [AUDIT.md](AUDIT.md) | Full audit report (dated) |

## One-paragraph summary

**Deutsch Essay Trainer** — B1–C1 German essay app. Vanilla HTML/JS frontend (nginx :8753) talks to FastAPI backend (:8000) + PostgreSQL. Users browse a thematic word list (`index.html`), plan/write essays (`schreiben.html`), and ops watch an autonomous word-enrichment pipeline (`pipeline.html`). Backend uses Mistral for word enrichment (+ essay API for future schreiben integration), Grok/DDG for article discovery.

## Production entry points

| URL | File | Backend |
|-----|------|---------|
| `/` | `index.html` | `GET /api/words` (optional overlay) |
| `/schreiben.html` | `schreiben.html` | none yet (localStorage) |
| `/pipeline.html` | `pipeline.html` | `/api/pipeline/*` |
| `/api/*` | — | all routes |
| `/health` | — | liveness |

## Do not waste tokens on

- `backend/scripts/`, `backend/audit_db.py` — manual maintenance CLIs
- `backend/data/` — local SQLite (gitignored)
- `graphify-out/` — generated code-graph artifact (gitignored); see [graph.md](graph.md) for how to use it
