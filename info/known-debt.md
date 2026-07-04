# Known tech debt (short)

Last updated: **2026-07-04**. Full audit: [`AUDIT.md`](AUDIT.md).

## High priority

| Issue | Where | Impact |
|-------|-------|--------|
| Pipeline v2 (runner) vs v3 (scripts) | `enrichment.py` vs `content_llm.py`/`verify.py` | Inconsistent `grammar_data` by write path |
| `normalize_grammar_data()` never called on write | `grammar_schema.py` vs `runner.py` | Messy grammar JSON in DB |
| No Alembic migrations | `main.py` `_ensure_new_columns` only | Schema drift in prod |
| Topic casing inconsistency | `pipeline.py` vs `runner.py` | Duplicate topic keys |
| **Dual essay flows** | `schreiben.js` (localStorage) vs `editor.js` (API) | Two parallel writing systems |

## Medium priority

| Issue | Where |
|-------|-------|
| `WORDS`/`WASH` triplicated | `app.js`, `editor.js`, `schreiben.js` |
| `schreiben.js` 1052 lines, no backend yet | localStorage store |
| 3 Wiktionary clients | `enrichment.py`, `wiktionary_client.py`, `backfill_grammar.py` |
| 2 Mistral HTTP stacks | `mistral_http.py` vs `mistral_analyzer.py` |
| `pipeline.html` inline JS | should be `js/pipeline.js` |
| `PIPELINE_*` env not in docker-compose | tuning blocked |
| Topic YAML packs missing | `/api/topics` empty in Docker |
| Tests mock pipeline I/O | no discovery/enrichment/extraction tests |
| `mistralai` in requirements, unused | `requirements.txt` |
| Docker mounts whole repo to nginx | dev-only; exposes `backend/` via :8753 |
| Large PNGs | `background_schreiben.png`, `autumn.png` |

## Low priority

| Issue | Where |
|-------|-------|
| Dead code: `_DDG_QUERIES`, `enrich_word()` | `discovery.py`, `enrichment.py` |
| `datetime.utcnow()` deprecated | pipeline modules |
| `@app.on_event` deprecated | `main.py` |
| `/health` doesn't check DB | `health.py` |
| Startup v1 cleanup every boot | `main.py` |
| Nav `href="#"` stubs | all HTML pages |
| `PIPELINE.md` partially stale | use `info/pipeline.md` |

## Resolved ✅

- Design System folder, `editor-extract`, `word-card.html` removed
- Nav Schreiben → `schreiben.html`
- Orphan PNGs: `roadmap-vine`, `mountains-corner`, `drawer-head-wash`
- README pytest count (36)

## Maintenance tools (keep)

- `backend/scripts/*`, `backend/audit_db.py`
