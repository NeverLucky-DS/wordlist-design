# Canonical file tree

Only files that matter for development/review.

**Verified against code: 2026-07-26.** Before this pass the tree still listed
`backend/app/pipeline/` and `backend/app/api/routes/` as covering
`topics`/`pipeline` — both packages are gone (removed 2026-07-06 and
2026-07-26, see "Removed" below). It also listed `js/app.js`, `js/animations.js`
and `css/styles.css`, all deleted 2026-07-26, and never mentioned
`backend/app/vocab/` at all — the largest backend package in the repo (21
Python modules) and the one the whole Wörterbuch product runs on.

```
wordlist design/
├── info/                    ← project docs (+ CRITICAL-LINKS.md, PLANS.md)
├── index.html               # Wörterbuch (search + personal word list)
├── schreiben.html           # Essay roadmap (Pomodoro, stages, Redemittel)
├── pipeline.html            # Vocab ingestion + enrichment ops dashboard
├── docker-compose.yml
├── nginx.conf
├── Dockerfile               # backend image (uv → uv.lock)
├── Makefile                 # setup/up/down/migrate/test/… (run `make`)
├── pyproject.toml           # Python deps + pytest config (single project, root)
├── uv.lock                  # pinned dependency lockfile
├── .python-version          # pins Python 3.11 for uv
├── README.md
├── GOLDEN-BACKUP.md          # why the untracked enrichment-GOLDEN-*.db backups must never be deleted
├── .github/workflows/pytest.yml   # CI: ruff (gate on all rules) + full pytest, all branches/PRs
│
├── css/
│   ├── woerterbuch.css      # index.html — "Разворот" layout, card, drawer
│   ├── schreiben.css        # schreiben.html
│   ├── pipeline.css         # pipeline.html
│   └── site-header.css      # Shared nav + theme toggle (all three pages)
│
├── js/
│   ├── words-data.js        # THE single WASH brush map (level×POS → worte/*.png); loaded by index + schreiben
│   ├── wb-card.js           # Wörterbuch card renderer (index.html)
│   ├── wb-page.js           # Wörterbuch page logic: search, drawer, personal list (index.html)
│   ├── schreiben.js         # Roadmap + editor + Wörterbuch-in-drawer logic
│   ├── schreiben-api.js     # Essay/version/analysis API bridge (owner-scoped)
│   ├── analysis-waiting-phrases.js  # Waiting-room copy shown during analysis
│   ├── pipeline.js          # Ingestion dashboard: /api/vocab/{build,status,stats,words,word}
│   ├── enrich.js            # Enrichment control panel: key, start/stop, progress, admin fleet
│   └── site-header.js       # Nav dropdown + theme toggle (shared)
│
├── images/                  # Decor PNGs (15 files) + images/header/ (4 files, shared nav art)
├── worte/                   # Brush PNGs by level×POS (15 files) — keys defined in js/words-data.js
│
├── scripts/
│   ├── hooks/               # Claude Code hooks: docker-guard, ruff-on-edit, frontend-on-edit, stop-checks — see info/tooling.md
│   └── ralph/               # Ralph autonomous-agent loop config (README.md, ralph.sh, ralph-settings.json)
│
├── tests/frontend/          # Playwright visual snapshots + asset-link integrity (pytest, run from repo root)
│
└── backend/
    ├── app/
    │   ├── main.py           # FastAPI app, CORS, router mounts, startup (seed + cleanup + mirror sync)
    │   ├── config.py         # Settings from env
    │   ├── auth.py           # Sessions (user + guest), Principal, require_user/require_admin
    │   ├── schemas.py        # Pydantic DTOs
    │   ├── api/
    │   │   ├── params.py     # Shared path-param types (int PK bounded to Postgres int32)
    │   │   └── routes/       # auth, essays, phrases, health — that's all of them now
    │   ├── services/         # essays_repo, phrases_repo, crypto, mistral_http, mistral_analyzer, analysis_jobs, user_stats_service, word_cleanup
    │   ├── db/                # models.py (schema), session.py, init_data.py (seed)
    │   └── vocab/             # dictionary ingestion + Mistral enrichment + Wörterbuch backend — see below
    ├── alembic/               # DB migrations (versions/) — single source of schema
    ├── alembic.ini
    ├── entrypoint.sh          # `alembic upgrade head` → uvicorn (container start)
    ├── tests/                 # pytest (backend/tests/*.py)
    ├── scripts/                # manual maintenance CLIs — do not run automatically (see CLAUDE.md)
    └── audit_db.py             # manual DB audit CLI
```

> uv project (`pyproject.toml`, `uv.lock`, `.venv/`) lives at the **repo root**,
> so `uv sync` / `uv run` work from anywhere. The app code stays in `backend/`.
> `pytest` runs both `backend/tests` and `tests/` (see `testpaths` in
> `pyproject.toml`).

## `backend/app/vocab/` — the biggest package, one per file

No LLM runs in `build.py`; Mistral only enters at `enrich.py`/`enrich_worker.py`.

| File | Role |
|------|------|
| `sources.py` | Registry of the bilingual dictionaries actually ingested (general + enrichment sources; Landeskunde/slang/technical excluded by design) |
| `dsl.py` | Dependency-free ABBYY Lingvo `.dsl`/`.dsl.dz` reader |
| `readers.py` | Unified reader over DSL + StarDict/MDX (via `pyglossary`) source formats |
| `goethe.py` | CEFR level from the Goethe/ÖSD wordlists — deliberately not from frequency |
| `data/*.tsv` | `goethe_levels.tsv`, `cefr_extra.tsv`, `cefr_manual.tsv` — the wordlists `goethe.py` reads |
| `build.py` | Deterministic ingestion run: dictionaries → `vocab.db`, wordfreq-ranked, no LLM |
| `demo_raw.py` | CLI: shows the raw per-word DSL payload before anything reaches Mistral |
| `show.py` | CLI: `vocab.db` stats + per-word card inspection |
| `topics.py` | ~150-topic catalog attached to words during enrichment |
| `intake.py` | Appends new headwords from a Wiktionary dump into `vocab.db` (`backend/scripts/import_new_words.py` drives it) |
| `funcwords.py` | Hand-written closed-class words (`der`, `die`, `im`, `zur`, …) the enrichment model refuses by design — zero tokens |
| `forms.py` | Tags headword vs. word-form entries (`form_kind`/`form_of`) so search can demote inflections/compounds |
| `enrich.py` | Server-side enrichment: phases (`PHASES`), claiming work, calling Mistral, parsing + storing cards into `enrichment.db` |
| `enrich_worker.py` | One background thread per authenticated account; calls Mistral via `app.services.mistral_http` with that account's key |
| `morph.py` | Imports full inflection paradigms from a German Wiktionary dump (`backend/scripts/import_morphology.py` drives it) |
| `norm.py` | Shared lemma normalization (case-fold, umlaut variants) for mirror/search/word list |
| `mirror.py` | Incremental replica: `enrichment.db` (SQLite, read-only) → Postgres `vocab_cards`/`vocab_card_translations` |
| `store.py` | Read helpers over `vocab.db` for the ops dashboard API |
| `api.py` | `/api/vocab/*` ops dashboard: build/status/stats, enrich start/stop/progress/cards/requeue, admin fleet |
| `dict_api.py` | `/api/vocab/*` Wörterbuch product API: search/entry/list — what `index.html` actually talks to |
| `requirements-vocab.txt` | Extra ingestion-only deps kept out of the root `pyproject.toml` |

## Removed (historical)

| Removed | Reason |
|---------|--------|
| `backend/app/pipeline/` (runner, scheduler, discovery, enrichment, extraction, supplement, normalize, verify, content_llm, …) + `api/routes/pipeline.py` | Legacy topic-discovery pipeline (Grok/DDG-driven); replaced by dictionary-based `backend/app/vocab/` (commit `039c585`) |
| `backend/app/api/routes/words.py`, `api/routes/topics.py` + `words_repo.py`, `grammar_parser.py`, `wiktionary_client.py`, `topic_pack_service.py` | Zero callers left after `js/app.js`/`js/editor.js` were deleted; `/api/topics` could only ever answer `[]`/404 (no `data/topics` dir shipped); `POST /{word_id}/refresh-grammar` had no auth dependency at all (commit `6444f36`) |
| `backend/app/vocab/server.py` | A second FastAPI app that served the real frontend statically on :8770 with a dev secret in code; unused, and `CRITICAL-LINKS.md` §6c already forbade a second way to run the frontend (removed in `a12cbaf`) |
| `js/app.js`, `js/animations.js`, `css/styles.css` | Not loaded by any of the three pages since the 2026-07-23 Wörterbuch rewrite; `images/Verwendung.png` was `styles.css`'s only reference and went with it (commit `ff1b26e`) |
| `prototypes/` (10 files, incl. `prototypes/woerterbuch/`) | Second door onto the same canon, served from a separate `python3 -m http.server` on :8799; the only supported way to run the frontend is `make up` (2026-07-25) |
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
- `backend/app/vocab/vocab_data/` — the real ingestion/enrichment SQLite DBs (docker-mounted). `backend/app/vocab/vocab.db*`/`enrichment.db*` (bare, no `vocab_data/`) are empty stub placeholders next to them — a script that resolves its DB path without `--enrich-db`/env override silently reads these instead and reports false "success" (see `CRITICAL-LINKS.md` §6a)
- `dictionaries/` — raw third-party dictionary dumps `build.py` ingests
- `enrichment-GOLDEN-*.db*`, `vocab-GOLDEN-*.db*` — backup snapshots of the enriched base; never delete from disk despite being untracked (see `GOLDEN-BACKUP.md`, which IS tracked)
- `.mcp.json` — contains a Postgres DSN with a password
- `__pycache__/`, `.venv/` (uv env lives at the repo root: `.venv/`)
- `graphify-out/` — generated code-graph (regenerate with `graphify`; see [graph.md](graph.md))
