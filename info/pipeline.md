# Pipeline (production v2)

Autonomous word + Redemittel enrichment per topic. Orchestrator: [`backend/app/pipeline/runner.py`](../backend/app/pipeline/runner.py).

## Control loop (per topic run)

```
discover_sources (Grok/DDG)
       ↓
process_sources (fetch HTML → extract words + phrases via Mistral)
       ↓
dedupe_candidates (normalize.py)
       ↓
_route_words (new vs existing in DB)
       ↓
enrich_batch (Wiktionary/DWDS + Mistral grammar, batched)
       ↓
_write_word / link topics
       ↓
[if words < target_words] supplement rounds (generate_words → verify Wiktionary)
       ↓
[if phrases < min_phrases] generate_redemittel
       ↓
retry word_failures from prior runs
```

## Modules

| Module | Role | Called by |
|--------|------|-----------|
| `discovery.py` | Find article URLs (Grok API, DDG fallback) | `runner` |
| `extraction.py` | Fetch articles, Mistral extract words+phrases | `runner` |
| `normalize.py` | Clean lemmas, strip articles, simplemma | `runner`, `extraction`, `supplement` |
| `enrichment.py` | Batch Mistral enrichment + Wiktionary wikitext | `runner` |
| `supplement.py` | Generate extra words/phrases to hit targets | `runner` |
| `mistral_http.py` | Shared Mistral POST with 429 retry/cooldown | enrichment, extraction, supplement, topics_catalog |
| `topics_catalog.py` | ~30 exam topics + LLM new topics | `scheduler` |
| `scheduler.py` | Background queue processor | `main.py` startup |
| `types.py` | Dataclasses: WordCandidate, EnrichedWord, etc. | all pipeline |

### Script-only modules (NOT in runner)

| Module | Used by |
|--------|---------|
| `content_llm.py` | `scripts/reprocess_topic.py` |
| `verify.py` | `scripts/reprocess_topic.py` |
| `wiktionary_grammar.py` | `scripts/backfill_grammar.py` |
| `grammar_schema.py` | `scripts/backfill_grammar.py` |

## Scheduler cycle ([`scheduler.py`](../backend/app/pipeline/scheduler.py))

When `pipeline_autorun=true`:

1. `recover_stale` — reset stuck queue items / failed runs
2. `maintenance_requeue` — re-queue under-target topics
3. `ensure_topics` — auto-fill queue from catalog + LLM
4. `process_next_topic` — run pipeline for next pending item

Interval: `pipeline_interval_minutes` (default 30).

## Config defaults ([`config.py`](../backend/app/config.py))

| Setting | Default |
|---------|---------|
| `pipeline_target_words` | 60 |
| `pipeline_min_phrases` | 12 |
| `pipeline_batch_size` | 6 |
| `pipeline_max_supplement_rounds` | 3 |
| `pipeline_max_attempts` | 3 |
| `pipeline_stale_run_minutes` | 120 |

## DB tables (pipeline-related)

See [data-model.md](data-model.md): `pipeline_runs`, `topic_queue_items`, `word_failures`, `word_topics`, `phrases`.

## Manual ops

```bash
# Queue topics
curl -X POST localhost:8000/api/pipeline/queue \
  -H 'Content-Type: application/json' \
  -d '{"topics":["Migration"],"target_words":60}'

# Dashboard
curl localhost:8000/api/pipeline/overview
```

Maintenance scripts (not in Docker CMD): `backend/scripts/cleanup_db.py`, `backfill_grammar.py`, `reprocess_topic.py`.
