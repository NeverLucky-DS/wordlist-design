# Known tech debt (short)

Last updated: **2026-07-13**. Full audit: [`AUDIT.md`](AUDIT.md). Safe-delete map: [`CRITICAL-LINKS.md`](CRITICAL-LINKS.md).

## High priority

| Issue | Where | Impact |
|-------|-------|--------|
| Pipeline v2 (runner) vs v3 (scripts) | `enrichment.py` vs `content_llm.py`/`verify.py` | Inconsistent `grammar_data` by write path |
| `normalize_grammar_data()` never called on write | `grammar_schema.py` vs `runner.py` | Messy grammar JSON in DB |
| Topic casing inconsistency | `pipeline.py` vs `runner.py` | Duplicate topic keys |

## Medium priority

| Issue | Where |
|-------|-------|
| Essay feedback precision not verified | `mistral_analyzer.py` — corrections + structure/argumentation are LLM-only, no verify-pass / rubric / citation-grounding yet |
| Open signup + guest AI has no quota | auth + essay analysis | Cost/abuse risk; private beta only |
| No email verification/password reset | auth | Email is a login identifier; lost passwords cannot be recovered in v1 |
| Analysis worker is in-process | `analysis_jobs.py` | Navigation survives, backend restart interrupts the run |
| `schreiben.js` ~1030 lines monolith | essay store, roadmap, tools |
| 3 Wiktionary clients | `enrichment.py`, `wiktionary_client.py`, `backfill_grammar.py` |
| 2 Mistral HTTP stacks | `mistral_http.py` vs `mistral_analyzer.py` |
| `PIPELINE_*` env not in docker-compose | tuning blocked |
| Topic YAML packs missing | `/api/topics` empty in Docker |
| Tests mock pipeline I/O | no discovery/enrichment/extraction tests |

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

## Resolved ✅ (2026-07-13 — accounts + essay persistence)

- **Accounts and ownership** — email/password sessions, 30-day guests, account
  deletion, guest claim on registration, owner-scoped essays/progress.
- **Schreiben split-brain** — server hydration, visible save states, manual retry,
  immutable versions and restore checkpoints.
- **Analysis history** — background full/part runs, polling after navigation,
  cancellation, partial warnings and stale-result markers.
- **Static exposure** — nginx now mounts only public frontend files.

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
