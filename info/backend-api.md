# Backend API

Base: `http://localhost:8000`. Interactive docs: `/docs`.

User data is scoped by an opaque `HttpOnly` session cookie. Visitors without an
account receive a 30-day guest session; registering claims that guest's essays.

## Auth

| Method | Path | Role |
|--------|------|------|
| GET | `/api/auth/me` | Current account or guest state |
| POST | `/api/auth/register` | Create email/password account and claim guest essays |
| POST | `/api/auth/login` | Start account session (does not claim guest data) |
| POST | `/api/auth/logout` | Revoke current session |
| DELETE | `/api/auth/account` | Delete account and owned data after password check |

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
| PATCH | `/api/essays/{id}` | Autosave text, structured sections and metadata |
| DELETE | `/api/essays/{id}` | Delete essay and all versions/analyses |
| POST/GET | `/api/essays/{id}/versions` | Create/list immutable checkpoints |
| POST | `/api/essays/{id}/versions/{version_id}/restore` | Restore while preserving current state |
| POST | `/api/essays/{id}/analyses` | Start background full/part analysis (202) |
| GET | `/api/essays/{id}/analyses` | Immutable analysis timeline |
| GET | `/api/essays/{id}/analyses/active` | Resume active run after navigation |
| GET | `/api/essays/{id}/analyses/{analysis_id}` | Poll status/result |
| POST | `/api/essays/{id}/analyses/{analysis_id}/cancel` | Request cooperative cancellation |
| GET | `/api/essays/{id}/analysis/latest` | Latest stored analysis |
| POST | `/api/essays/{id}/analyze` | Legacy synchronous compatibility endpoint |
| POST | `/api/essays/{id}/analyze/stream` | Legacy SSE compatibility endpoint |

**Services:** `analysis_jobs.py` owns in-process runs and database status;
`mistral_analyzer.py` emits part events and uses the shared Mistral retry/cooldown.

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

All pipeline routes require an authenticated email listed in `ADMIN_EMAILS`.

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
| `essays_repo.py` | Owner-scoped essay/version/analysis persistence |
| `analysis_jobs.py` | Background analysis lifecycle and cancellation |
| `words_repo.py` | Word queries |
| `phrases_repo.py` | Phrase queries |
| `user_stats_service.py` | Authenticated per-user progress stats |
| `topic_pack_service.py` | YAML import, lemma fix, dedupe, topic linking |
| `mistral_analyzer.py` | Essay analysis prompts + streaming |
| `wiktionary_client.py` | REST Wiktionary for refresh-grammar |
| `grammar_parser.py` | Parse Wiktionary JSON → grammar_data |
