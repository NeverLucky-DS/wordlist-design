# Backend API

Base: `http://localhost:8000`. Interactive docs: `/docs`.

User data is scoped by an opaque `HttpOnly` session cookie. Visitors without an
account receive a 30-day guest session; registering claims that guest's essays.

**Проверено против кода: 2026-07-26.** Раньше файл документировал семь ручек
`/api/pipeline/*` и по одной ручке `words`/`topics`/`phrases`, которых больше
нет (роутеры `words.py`, `topics.py`, `pipeline.py` и пакет
`backend/app/pipeline/` удалены), и не описывал ни одной из 24 живых ручек
`/api/vocab/*`. Список ниже собран из `app.main.app.openapi()['paths']`
(`uv run python -c "..."`, см. команду в `info/tooling.md`/PLANS §A8) и сверен
построчно с `@router.` в коде — не с памятью.

## Routers mounted (`backend/app/main.py`)

Exactly six: `health`, `auth`, `essays`, `phrases`, `vocab` (`app/vocab/api.py`),
`woerterbuch` (`app/vocab/dict_api.py`). No `words`, `topics` or `pipeline`
router is imported or included — those source files do not exist in the repo.

## Health

| Method | Path | Handler | Returns |
|--------|------|---------|---------|
| GET | `/health` | `api/routes/health.py` | `{"status":"ok"}` |

## Auth — [`api/routes/auth.py`](../backend/app/api/routes/auth.py)

| Method | Path | Auth | Role |
|--------|------|------|------|
| GET | `/api/auth/me` | `get_principal` (auto-creates guest) | Current account or guest state |
| PUT | `/api/auth/mistral-key` | `require_user` | Attach/replace this account's Mistral key (encrypted at rest) |
| DELETE | `/api/auth/mistral-key` | `require_user` | Detach the stored key |
| POST | `/api/auth/register` | `get_principal` | Create email/password account and claim guest essays |
| POST | `/api/auth/login` | none (issues session) | Start account session (does not claim guest data) |
| POST | `/api/auth/logout` | none | Revoke current session |
| DELETE | `/api/auth/account` | `require_user` | Delete account and owned data after password check |

`require_admin` = `require_user` + `email` in server-config `ADMIN_EMAILS`
(`is_admin_email()`, `app/auth.py:161`). No endpoint grants admin; it is
env-only, on purpose — an admin drives enrichment through *other* accounts'
Mistral keys.

## Essays — [`api/routes/essays.py`](../backend/app/api/routes/essays.py)

All routes take `principal: Principal = Depends(get_principal)` — essays work
for guests too (localStorage-free; the guest session cookie is the identity),
unlike the vocab word list below which has no guest mode.

| Method | Path | Role |
|--------|------|------|
| POST | `/api/essays` | Create essay |
| GET | `/api/essays` | List essays |
| GET | `/api/essays/{essay_id}` | Get essay |
| PATCH | `/api/essays/{essay_id}` | Autosave text, structured sections and metadata |
| DELETE | `/api/essays/{essay_id}` | Delete essay and all versions/analyses |
| POST | `/api/essays/{essay_id}/versions` | Create immutable checkpoint |
| GET | `/api/essays/{essay_id}/versions` | List checkpoints |
| POST | `/api/essays/{essay_id}/versions/{version_id}/restore` | Restore while preserving current state |
| POST | `/api/essays/{essay_id}/analyses` | Start background full/part analysis (202) |
| GET | `/api/essays/{essay_id}/analyses` | Immutable analysis timeline |
| GET | `/api/essays/{essay_id}/analyses/active` | Resume active run after navigation |
| GET | `/api/essays/{essay_id}/analyses/{analysis_id}` | Poll status/result |
| POST | `/api/essays/{essay_id}/analyses/{analysis_id}/cancel` | Request cooperative cancellation |
| GET | `/api/essays/{essay_id}/analysis/latest` | Latest stored analysis (legacy shape) |
| POST | `/api/essays/{essay_id}/analyze` | Legacy synchronous compatibility endpoint |
| POST | `/api/essays/{essay_id}/analyze/stream` | Legacy SSE compatibility endpoint |

**Called by:** `js/schreiben-api.js` (all of the above), consumed by
`js/schreiben.js`.

**Services:** `essays_repo.py` (owner-scoped persistence), `analysis_jobs.py`
(in-process run lifecycle + cancellation, calls `user_stats_service.py` to
record streaks), `mistral_analyzer.py` (prompts + streaming, shared
`app/services/mistral_http.py` retry/cooldown).

⚠️ `essay_id`/`version_id`/`analysis_id` are plain `int` path params with no
upper bound — see `info/PLANS.md` A8 for the resulting `OverflowError` → 500 on
an out-of-range id.

## Phrases (Redemittel) — [`api/routes/phrases.py`](../backend/app/api/routes/phrases.py)

`GET /api/phrases` (list-all, no auth) from the old doc **does not exist**.
The router now has exactly two routes, both under `/api/phrases`:

| Method | Path | Auth | Query | Role |
|--------|------|------|-------|------|
| GET | `/api/phrases/templates` | `get_principal` | `level`, `part` | Deduplicated essay-part clichés (see below) |
| POST | `/api/phrases/{phrase_id}/known` | `require_user` | — | Mark a phrase as known for this account |

`list_templates` (`phrases_repo.py`) collapses the `phrases` table — which
stores one row per essay prompt it was generated for — down to distinct
wordings *within an essay part* (a wording can legitimately belong to more
than one part), keeps only rows whose German text contains the `...`
placeholder (the signal that separates a reusable template from a one-off
content sentence), and orders shortest-first. No `topic` query param exists;
templates are topic-independent by design.

**Called by:** `js/schreiben.js` (`loadKlischees`, `kliFiltered`, pager).

## Vocab — dictionary-ingestion dashboard — [`app/vocab/api.py`](../backend/app/vocab/api.py)

Reads a **SQLite** `vocab.db` (raw, pre-enrichment dictionary dump written by
`build.py`) plus the enrichment tables in `enrichment.db`. See
`info/pipeline.md` for how the two databases and the worker relate.

| Method | Path | Auth | Query/Body | Role |
|--------|------|------|------------|------|
| POST | `/api/vocab/build` | `require_admin` | `min_zipf` (default 2.3) | Rebuild `vocab.db` from the dictionary dumps from scratch (`db_path.unlink()` first — destructive) |
| GET | `/api/vocab/status` | public | — | Current/last build job progress (in-memory) |
| GET | `/api/vocab/stats` | public | — | Build totals: per-level counts, per-field coverage |
| GET | `/api/vocab/words` | public | `q`, `level`, `limit` | Search the raw `vocab.db` word list |
| GET | `/api/vocab/word/{lemma}` | public | — | One raw dictionary entry, with per-source breakdown |
| POST | `/api/vocab/enrich/start` | `require_user` | `{batch?}` | Start *this account's* enrichment worker with its own stored Mistral key |
| POST | `/api/vocab/enrich/stop` | `require_user` | — | Stop this account's worker |
| GET | `/api/vocab/enrich/progress` | public | — | Global enrichment progress + summaries of active workers |
| GET | `/api/vocab/enrich/cards` | public | `q`, `confidence`, `topic`, `level`, `limit`, `offset` | Browse enriched cards (the output the app shows) |
| GET | `/api/vocab/enrich/card/{lemma}` | public | — | One enriched card |
| POST | `/api/vocab/enrich/requeue` | `require_user`\* | `{scope?, lemmas?}` | Reset cards to re-enrich with the current prompt |
| GET | `/api/vocab/enrich/fleet` | `require_admin` | — | Every account's worker state + token spend |
| POST | `/api/vocab/enrich/fleet/start` | `require_admin` | `{batch?}` | Start a worker for every account that has a key attached |
| POST | `/api/vocab/enrich/fleet/stop` | `require_admin` | — | Stop every running worker, whoever started it |
| GET | `/api/vocab/enrich/status` | `require_user` | — | This account's own worker state |

\* `enrich/requeue`: `scope="low_confidence"` is open to any logged-in user
(bounded — 18 cards on the live base). An explicit `lemmas` list additionally
requires `is_admin_email()` in-handler, because `enrich.requeue` defaults to
`drop_card=True` — a large list is effectively a DELETE of the dictionary, and
signup needs no e-mail confirmation.

**Called by:** `js/pipeline.js` (`build`/`status`/`stats`/`words`/`word`),
`js/enrich.js` (everything under `enrich/*` plus `PUT`/`DELETE
/api/auth/mistral-key`).

## Vocab — Wörterbuch product API — [`app/vocab/dict_api.py`](../backend/app/vocab/dict_api.py)

Reads the **Postgres** mirror (`vocab_cards`, `vocab_card_translations`) that
`app/vocab/mirror.py` copies from `enrichment.db`, plus `user_word_list`. Same
`/api/vocab` prefix as the table above — FastAPI merges both routers.

| Method | Path | Auth | Query/Body | Role |
|--------|------|------|------------|------|
| GET | `/api/vocab/search` | optional (`get_optional_user`) | `q`, `limit` (≤ 50) | Fuzzy lookup: Latin → German lemma, Cyrillic → Russian meaning |
| GET | `/api/vocab/entry/{lemma}` | optional | — | One full card by exact lemma (path allows `/`) |
| GET | `/api/vocab/list` | `require_user` | `limit` (≤ 100), `offset` | This account's word list, newest first |
| GET | `/api/vocab/list/stats` | `require_user` | — | Word-list counts per `band` |
| POST | `/api/vocab/list` | `require_user` | `{lemma}` | Add a word (idempotent snapshot upsert) |
| DELETE | `/api/vocab/list/{lemma}` | `require_user` | — | Remove a word from the list |
| POST | `/api/vocab/mirror/sync` | `require_admin` | — | Manual nudge of the SQLite→Postgres replica (also runs on a 5 min timer) |

There is **no guest mode** for the personal list (unlike essays) — `require_user`
throughout. `search`/`entry` are public reads; when a `principal` is present the
response is annotated with `in_list`.

**Called by:** `js/wb-page.js` (`search`, `entry`, `list` GET/POST,
`list/stats`, `list/{lemma}` DELETE) — loaded by `index.html` together with
`js/wb-card.js`. `mirror/sync` has no frontend caller; it is an ops-only route
(curl/`/docs`).

## Services quick map

| Module | Responsibility |
|--------|----------------|
| `essays_repo.py` | Owner-scoped essay/version/analysis persistence |
| `analysis_jobs.py` | Background analysis lifecycle and cancellation |
| `mistral_analyzer.py` | Essay analysis prompts + streaming |
| `user_stats_service.py` | Streak/progress bookkeeping, called from `analysis_jobs.py` (no route of its own) |
| `phrases_repo.py` | Cliché template queries + per-user known-flag |
| `crypto.py` | Encrypt/decrypt the per-account Mistral key (`MISTRAL_KEY_SECRET`) |
| `app/vocab/store.py` | Read helpers over `vocab.db` for the ingestion dashboard |
| `app/vocab/enrich.py` | Enrichment format, storage, phases, prompt version |
| `app/vocab/enrich_worker.py` | One background thread per authenticated account |
| `app/vocab/search.py` | Postgres `pg_trgm` lookup + ranking |
| `app/vocab/mirror.py` | Incremental SQLite → Postgres replica |

`words_repo.py`, `topic_pack_service.py`, `wiktionary_client.py` and
`grammar_parser.py` from the old version of this file **do not exist** —
they backed the `words`/`topics` routers, which are gone.
