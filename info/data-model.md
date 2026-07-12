# Data model

Source: [`backend/app/db/models.py`](../backend/app/db/models.py). JSON columns use JSONB on Postgres.

## Core entities

### `users`, `auth_sessions`, `guest_sessions`
Accounts use normalized email + Argon2id password hashes. Opaque session tokens
are stored only as SHA-256 hashes. Guest sessions expire after 30 days and own
the same essay graph until registration claims it.

### `essays`
Current editable state. Exactly one of `user_id` or `guest_session_id` is set.
`text` is the analyzer format; `content_json` preserves per-stage drafts and task.

### `essay_versions`
Immutable checkpoints containing title, flat text and structured content.
Created manually, immediately before analysis, and before restoring an older
version.

### `essay_analyses`
Immutable run/result linked to the exact `essay_version`. Relational columns hold
scope, part, status, progress, model/schema/prompt versions and timestamps;
variable feedback stays in JSONB (`errors_json`, `part_reports_json`,
`final_summary_json`, `warnings_json`). Statuses include queued, running,
completed, completed_with_warnings, cancelled, interrupted and failed.

### `words`
German vocabulary entries.

| Column | Notes |
|--------|-------|
| `german` | Lemma (lowercase, no article prefix) |
| `article` | der/die/das or null |
| `word_type` | noun, verb, adj, … |
| `translation_ru` | Russian gloss |
| `level` | B1/B2/C1 |
| `grammar_data` | JSON — declension, cases, verb forms |
| `examples` | JSON array |
| `source` | seed_csv, pipeline, … |

### `word_topics`
M2M: word ↔ topic string. Unique on `(word_id, topic)`.

### `phrases`
Redemittel / essay clichés.

| Column | Notes |
|--------|-------|
| `german` | Phrase text |
| `topic` | Theme |
| `level` | B1/B2/C1 |
| `essay_part` | einleitung, argument, … |
| `translation_ru` | optional |

### `pipeline_runs`
Audit log per pipeline execution.

| Column | Notes |
|--------|-------|
| `topic` | May differ in casing from normalized links |
| `status` | running, completed, failed |
| `words_added`, `words_linked`, `phrases_added` | counters |
| `target_words` | goal for this run |
| `errors_json` | list of error dicts |

### `topic_queue_items`
Autonomous scheduler queue.

| Column | Notes |
|--------|-------|
| `topic` | |
| `status` | pending, running, done, failed |
| `target_words` | optional override |
| `attempts` | retry count |
| `last_run_id` | FK pipeline_runs |

### `word_failures`
Words that failed enrichment; auto-retried on next run (max 3 attempts).

### User progress

| Table | Role |
|-------|------|
| `user_word_progress` | Words queued/known per user |
| `user_phrase_known` | Known phrases |
| `user_stats` | Daily counters |

All `user_id` columns reference `users.id`; guest essay analysis does not create
account streak/progress rows.

## Conventions

- **Topics:** runner lowercases; API `/run` may preserve case → potential duplicates
- **Words:** article separate from `german` lemma after v2 normalization
- **grammar_data:** intended schema in `grammar_schema.py` but **not enforced on write** in production runner
