# Known tech debt (short)

> ⚠️ **Superseded on 2026-07-26.** The live debt list now lives in
> [`AUDIT-2026-07-26.md`](AUDIT-2026-07-26.md) (priorities, with a measurement per
> item) and in [`PLANS.md`](PLANS.md) (the work queue). This file is kept for the
> "Resolved" log below, which is still accurate history.
>
> What was here until today described the topic pipeline, and **all seven files it
> named are gone**: `runner.py`, `enrichment.py`, `grammar_schema.py`,
> `content_llm.py`, `verify.py`, `discovery.py`, `backfill_grammar.py`. Anyone who
> started their cleanup from this page — the page `info/README.md` points at for
> "remaining tech debt" — was fixing a subsystem that no longer exists. Two more
> entries had rotted the same way: `schreiben.js` was listed at "~1030 lines"
> (it is 2377) and nav `href="#"` stubs were listed as open (there are 0).

## Still open, and not tracked anywhere else

These survived the rewrite because they are real and current — everything else
moved to the audit:

| Issue | Where |
|-------|-------|
| Essay feedback precision not verified | `mistral_analyzer.py` — corrections + structure/argumentation are LLM-only, no verify-pass / rubric / citation-grounding |
| Open signup + guest AI has no quota | auth + essay analysis; cost/abuse risk, private beta only. Measured 2026-07-26: `/analyze*` runs on the owner's shared key for anonymous guests |
| No email verification / password reset | auth — email is the login identifier, a lost password cannot be recovered |
| Analysis worker is in-process | `analysis_jobs.py` — navigation survives, a backend restart interrupts the run |
| 2 Mistral HTTP stacks | `mistral_http.py` vs `mistral_analyzer.py` |
| `@app.on_event` deprecated | `main.py` — warns on every test run |
| `/health` doesn't check DB | `health.py` |

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
