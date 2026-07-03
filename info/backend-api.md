# Backend API

Base: `http://localhost:8000`. Interactive docs: `/docs`.

All routes use `default_user_id=1` from config (no auth).

## Health

| Method | Path | Handler | Returns |
|--------|------|---------|---------|
| GET | `/health` | `health.py` | `{"status":"ok"}` |

## Essays — [`api/routes/essays.py`](../backend/app/api/routes/essays.py)

| Method | Path | Role |
|--------|------|------|
| POST | `/api/essays` | Create essay |
| GET | `/api/essays` | List essays |
| GET | `/api/essays/{id}` | Get essay |
| PATCH | `/api/essays/{id}` | Update title/text/topic/level |
| GET | `/api/essays/{id}/analysis/latest` | Latest stored analysis |
| POST | `/api/essays/{id}/analyze` | Sync Mistral analysis |
| POST | `/api/essays/{id}/analyze/stream` | SSE stream of analysis events |

**Service:** [`services/mistral_analyzer.py`](../backend/app/services/mistral_analyzer.py) — separate httpx client (no shared 429 cooldown with pipeline).

## Words — [`api/routes/words.py`](../backend/app/api/routes/words.py)

| Method | Path | Query params | Role |
|--------|------|--------------|------|
| GET | `/api/words` | `topic`, `level`, `q` | Filtered word list |
| GET | `/api/words/{id}` | — | Single word |
| POST | `/api/words/{id}/queue` | — | Queue word's topics for pipeline |
| POST | `/api/words/{id}/refresh-grammar` | — | Re-fetch grammar via REST Wiktionary |

**Services:** `words_repo.py`, `grammar_parser.py`, `wiktionary_client.py`, `topic_pack_service.py`

## Phrases (Redemittel) — [`api/routes/phrases.py`](../backend/app/api/routes/phrases.py)

| Method | Path | Query | Role |
|--------|------|-------|------|
| GET | `/api/phrases` | `topic`, `level`, `part` | Clichés for essay sections |
| POST | `/api/phrases/{id}/known` | — | Mark phrase as known |

## Topics — [`api/routes/topics.py`](../backend/app/api/routes/topics.py)

| Method | Path | Role |
|--------|------|------|
| GET | `/api/topics` | List topic summaries |
| GET | `/api/topics/{slug}` | Topic pack detail |
| POST | `/api/topics/{slug}/import` | Import from `.topic.yaml` |

**Note:** `data/topics/*.topic.yaml` not in repo; `TOPICS_DIR` defaults to `/data/topics` (not mounted in Docker). Topics mainly come from pipeline DB.

## Pipeline — [`api/routes/pipeline.py`](../backend/app/api/routes/pipeline.py)

| Method | Path | Role |
|--------|------|------|
| POST | `/api/pipeline/run` | Start pipeline for one topic (`topic`, `article_urls?`, `target_words?`) |
| POST | `/api/pipeline/queue` | Queue topics for scheduler (`topics[]`, `target_words?`) |
| GET | `/api/pipeline/queue` | List queue items |
| GET | `/api/pipeline/overview` | Dashboard: word/phrase counts, queue, failures, settings |
| GET | `/api/pipeline/failures` | Open `word_failures` |
| GET | `/api/pipeline/run/{run_id}` | Poll single run |
| GET | `/api/pipeline/runs` | Run history |

**Runner:** [`pipeline/runner.py`](../backend/app/pipeline/runner.py) via `BackgroundTasks`.

## Services quick map

| Module | Responsibility |
|--------|----------------|
| `essays_repo.py` | Essay CRUD |
| `words_repo.py` | Word queries |
| `phrases_repo.py` | Phrase queries |
| `user_stats_service.py` | Progress stats (user_id=1) |
| `topic_pack_service.py` | YAML import, lemma fix, dedupe, topic linking |
| `mistral_analyzer.py` | Essay analysis prompts + streaming |
| `wiktionary_client.py` | REST Wiktionary for refresh-grammar |
| `grammar_parser.py` | Parse Wiktionary JSON → grammar_data |
