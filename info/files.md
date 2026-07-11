# Canonical file tree

Only files that matter for development/review.

```
wordlist design/
├── info/                    ← project docs (+ CRITICAL-LINKS.md)
├── index.html               # Wörterbuch
├── schreiben.html           # Essay roadmap (Pomodoro, stages)
├── pipeline.html            # Pipeline dashboard
├── docker-compose.yml
├── nginx.conf
├── Dockerfile               # backend image (uv → uv.lock)
├── Makefile                 # setup/up/down/migrate/test/… (run `make`)
├── pyproject.toml           # Python deps + pytest config (single project, root)
├── uv.lock                  # pinned dependency lockfile
├── .python-version          # pins Python 3.11 for uv
├── README.md
│
├── css/
│   ├── styles.css           # Wörterbuch
│   ├── schreiben.css        # Schreiben page
│   ├── pipeline.css         # Pipeline dashboard
│   └── site-header.css      # Shared nav (index, pipeline)
│
├── js/
│   ├── words-data.js        # Shared WASH + brushOf + PIPELINE_WASHES
│   ├── app.js               # Wörterbuch logic
│   ├── schreiben.js         # Roadmap logic
│   ├── pipeline.js          # Pipeline dashboard logic
│   ├── site-header.js       # Nav dropdown + theme toggle
│   └── animations.js        # index.html animations
│
├── images/                  # Decor PNGs (15 files)
├── worte/                   # Brush PNGs by level×POS (15 files)
│
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── schemas.py
    │   ├── api/routes/      # essays, words, phrases, topics, pipeline, health
    │   ├── services/        # repos + mistral_analyzer + wiktionary
    │   ├── db/              # models, session, init_data
    │   └── pipeline/        # runner, scheduler, discovery, enrichment, …
    ├── alembic/            # DB migrations (versions/) — single source of schema
    ├── alembic.ini
    ├── entrypoint.sh       # `alembic upgrade head` → uvicorn (container start)
    ├── tests/              # pytest (36 tests)
    ├── scripts/            # manual maintenance only
    └── audit_db.py         # manual DB audit CLI
```

> uv project (`pyproject.toml`, `uv.lock`, `.venv/`) lives at the **repo root**,
> so `uv sync` / `uv run` work from anywhere. The app code stays in `backend/`.

## Removed (historical)

| Removed | Reason |
|---------|--------|
| `editor.html`, `editor.js`, `editor-api.js`, `editor.css` | Legacy parallel essay flow; not in nav |
| `images/autumn.png` | Editor-only asset |
| `screenshots/` | README demo images; not in UI |
| `Deutsch Essay Design System/` | Duplicate assets; not deployed |
| `editor-extract/` | Incomplete React stub |
| `word-card.html`, `screenshots/Deutsch_2.png` | Orphans |
| `images/roadmap-vine.png`, `mountains-corner.png`, `drawer-head-wash.png` | Unreferenced |
| `PIPELINE.md` | Superseded by `info/pipeline.md`; long + partially stale (removed 2026-07-06) |
| `backend/requirements.txt`, `backend/pytest.ini` | Superseded by root `pyproject.toml` + `uv.lock` (uv migration, 2026-07-10) |
| root `.env` | Redundant — secrets unified into `backend/.env` (docker reads it via `env_file`); removed 2026-07-10 |
| `create_all` + `_ensure_new_columns` in `app/main.py` | Schema now owned by Alembic migrations (2026-07-10) |

## Gitignored (local only)

- `backend/.env` — single config/secrets file (copy from `backend/.env.example`)
- `backend/data/*.db`
- `__pycache__/`, `.venv/` (uv env lives at the repo root: `.venv/`)
- `graphify-out/` — generated code-graph (regenerate with `graphify`; see [graph.md](graph.md))
