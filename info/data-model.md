# Data model

Source: [`backend/app/db/models.py`](../backend/app/db/models.py). JSON columns use JSONB on Postgres.

## Core entities

### `essays`
User essays. Fields: `title`, `text`, `essay_type`, `topic`, `level`, timestamps.

### `essay_analyses`
Mistral analysis results per essay. `errors_json`, `part_reports_json`, `final_summary_json`, `overall_score`, `grade`, `text_snapshot`.

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

### User progress (single-user prototype)

| Table | Role |
|-------|------|
| `user_word_progress` | Words queued/known per user |
| `user_phrase_known` | Known phrases |
| `user_stats` | Daily counters |

All use `user_id` — hardcoded to `1` in API.

## Conventions

- **Topics:** runner lowercases; API `/run` may preserve case → potential duplicates
- **Words:** article separate from `german` lemma after v2 normalization
- **grammar_data:** intended schema in `grammar_schema.py` but **not enforced on write** in production runner
