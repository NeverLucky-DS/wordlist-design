# Known tech debt (short)

Last updated: **2026-07-10**. Full audit: [`AUDIT.md`](AUDIT.md). Safe-delete map: [`CRITICAL-LINKS.md`](CRITICAL-LINKS.md).

## High priority

| Issue | Where | Impact |
|-------|-------|--------|
| Pipeline v2 (runner) vs v3 (scripts) | `enrichment.py` vs `content_llm.py`/`verify.py` | Inconsistent `grammar_data` by write path |
| `normalize_grammar_data()` never called on write | `grammar_schema.py` vs `runner.py` | Messy grammar JSON in DB |
| Topic casing inconsistency | `pipeline.py` vs `runner.py` | Duplicate topic keys |
| **schreiben ↔ backend (частично)** | `schreiben.js` + `schreiben-api.js` | Essays + анализ через API; UI/список essays ещё localStorage |

## Medium priority

| Issue | Where |
|-------|-------|
| Essay feedback precision not verified | `mistral_analyzer.py` — corrections + structure/argumentation are LLM-only, no verify-pass / rubric / citation-grounding yet |
| `schreiben.js` ~1030 lines monolith | essay store, roadmap, tools |
| 3 Wiktionary clients | `enrichment.py`, `wiktionary_client.py`, `backfill_grammar.py` |
| 2 Mistral HTTP stacks | `mistral_http.py` vs `mistral_analyzer.py` |
| `PIPELINE_*` env not in docker-compose | tuning blocked |
| Topic YAML packs missing | `/api/topics` empty in Docker |
| Tests mock pipeline I/O | no discovery/enrichment/extraction tests |
| Docker mounts whole repo to nginx | dev-only; exposes `backend/` via :8753 |
| `schreiben.html` без `site-header.css` | theme toggle частично (site-header.js подключён) |

## Low priority

| Issue | Where |
|-------|-------|
| `datetime.utcnow()` deprecated | pipeline modules |
| `@app.on_event` deprecated | `main.py` |
| `/health` doesn't check DB | `health.py` |
| Startup v1 cleanup every boot | `main.py` |
| Nav `href="#"` stubs | all HTML pages |

## Resolved ✅ (2026-07-10 — migrations + tooling)

- **Alembic migrations** — schema now versioned in `backend/alembic/`; `create_all` + `_ensure_new_columns` hack removed from `main.py`. Applied by container entrypoint (`alembic upgrade head`). Models stay source of truth; `make migration`/`make migrate` for changes.
- **uv + pyproject.toml** — replaced `requirements.txt` + `pytest.ini`; `uv.lock` pins deps; Dockerfile + CI use uv.
- **Single `.env`** — root `.env` removed; secrets unified into `backend/.env` (docker reads via `env_file`).
- **`Makefile`** — one-command lifecycle: `make setup`/`up`/`down`/`migrate`/`test`/`logs`/`db`/`clean`.
- **Backend healthcheck** — compose waits for `/health` before marking backend ready.

## Resolved ✅ (2026-07-06 cleanup)

- **Dead code removed** — `_DDG_QUERIES` (`discovery.py`), `enrich_word()` wrapper (`enrichment.py`)
- **`PIPELINE.md` removed** — superseded by `info/pipeline.md`
- **`graphify-out/` gitignored** — generated code-graph, regenerable; docs in `info/graph.md`

## Resolved ✅ (2026-07-04 cleanup)

- **Editor stack removed** — `editor.html`, `editor.js`, `editor-api.js`, `editor.css`, `autumn.png`
- **`WORDS`/`WASH` deduped** → `js/words-data.js` (index, schreiben, pipeline)
- **`pipeline.html` inline JS** → `js/pipeline.js`
- **`schreiben-api.js` + analyze SSE** — essays sync + Mistral stream wired (2026-07-04)
- **`screenshots/` removed** (README no longer depends on demo PNGs)
- Nav Schreiben → `schreiben.html`
- Orphan PNGs: `roadmap-vine`, `mountains-corner`, `drawer-head-wash`

## Maintenance tools (keep)

- `backend/scripts/*`, `backend/audit_db.py`
