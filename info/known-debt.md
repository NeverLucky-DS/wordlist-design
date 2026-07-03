# Known tech debt (short)

Post-cleanup snapshot. Full historical audit was in `TECH_DEBT_AUDIT.md` (removed).

## High priority

| Issue | Where | Impact |
|-------|-------|--------|
| Pipeline v2 (runner) vs v3 (scripts) | `enrichment.py` vs `content_llm.py`/`verify.py` | Inconsistent `grammar_data` depending on write path |
| `normalize_grammar_data()` never called on write | `grammar_schema.py` vs `runner.py` | Frontend may get messy grammar JSON |
| No Alembic migrations | `main.py` `_ensure_new_columns` only | Schema drift in prod |
| Topic casing inconsistency | `pipeline.py` vs `runner.py` | Duplicate topic keys in DB |

## Medium priority

| Issue | Where |
|-------|-------|
| 3 Wiktionary clients | `enrichment.py`, `wiktionary_client.py`, `backfill_grammar.py` |
| 2 Mistral HTTP stacks | `mistral_http.py` vs `mistral_analyzer.py` |
| `schreiben.html` not linked from nav | `index.html`, `pipeline.html` still → `editor.html` |
| `pipeline.html` inline JS (~350 lines) | should be `js/pipeline.js` |
| `PIPELINE_*` env not in docker-compose | can't tune without code change |
| Topic YAML packs missing | `/api/topics` empty in Docker |
| Tests mock pipeline I/O | no tests for discovery/enrichment/extraction |
| README says pytest (16) | actually 36 |

## Low priority

| Issue | Where |
|-------|-------|
| Dead code: `_DDG_QUERIES`, `enrich_word()` | `discovery.py`, `enrichment.py` |
| `datetime.utcnow()` deprecated | multiple files |
| `@app.on_event` deprecated | `main.py` |
| `/health` doesn't check DB | `health.py` |
| Startup cleanup every boot | `main.py` (v1 legacy) |

## Maintenance tools (keep, not wired to CI)

- `backend/scripts/cleanup_db.py`
- `backend/scripts/backfill_grammar.py`
- `backend/scripts/reprocess_topic.py`
- `backend/audit_db.py`
