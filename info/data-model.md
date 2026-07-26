# Data model

**Verified against code: 2026-07-26.** Before this pass the file documented
three tables a migration had already dropped (`pipeline_runs`,
`topic_queue_items`, `word_failures` — dropped by
`backend/alembic/versions/b3f8c1d2e4a5_drop_topic_pipeline_tables.py`,
2026-07-13) and never mentioned the three tables the Wörterbuch actually runs
on (`vocab_cards`, `vocab_card_translations`, `user_word_list`), added two days
later by `88b9d9797836_woerterbuch_mirror_and_word_list.py` (2026-07-15). It
also named the wrong column on `phrases` (`german` instead of `text_de`).

Source of truth: [`backend/app/db/models.py`](../backend/app/db/models.py).
Schema itself is owned by Alembic (`backend/alembic/versions/`); `models.py`
must stay in sync with the latest migration by hand — see the comment on
`VocabCard.__table_args__` for why every index has to be declared there too,
not only in a migration (`alembic check` on a fresh DB otherwise proposes
dropping the three GIN trigram indexes search depends on). JSON columns use
`JSON().with_variant(JSONB, "postgresql")` throughout, so Postgres stores them
as JSONB while the sqlite test DBs still work.

## Accounts & sessions

### `users`, `auth_sessions`, `guest_sessions`
Accounts use normalized email + Argon2id password hashes (`pwdlib`). Opaque
session tokens are stored only as SHA-256 hashes (`token_hash`), never in the
clear. `users.mistral_key_enc` holds a per-user Mistral API key encrypted at
rest with Fernet (`app/services/crypto.py`); it is used only by the
server-side vocab enrichment worker and never returned to a client. Both
session kinds currently expire after 30 days (`AUTH_DAYS` / `GUEST_DAYS` in
`app/auth.py`); a guest session owns an essay until registration claims it.

## Essays

### `essays`
Current editable state. A `CHECK` constraint (`ck_essay_exactly_one_owner`)
enforces that exactly one of `user_id` / `guest_session_id` is set. `text` is
the flat analyzer format; `content_json` preserves the per-stage draft plus
task metadata that the editor UI needs.

### `essay_versions`
Immutable checkpoint: title, flat text, structured content. `reason` is one
of `manual` (explicit save), `analysis` (taken right before an analysis run),
or `pre_restore` (taken right before restoring an older version) — enforced
in `POST /{essay_id}/versions` and set by `essays_repo.create_version`.

### `essay_analyses`
Immutable run/result linked to the `essay_version` it graded. Relational
columns hold scope, part, status, progress step, `model`/`schema_version`/
`prompt_version` and timestamps; variable feedback stays in JSONB
(`errors_json`, `part_reports_json`, `final_summary_json`, `warnings_json`).
`status` values, from `app/services/analysis_jobs.py`: `queued`, `running`,
`completed`, `completed_with_warnings`, `cancelled`, `interrupted`, `failed`
(`interrupted` is also what a container restart stamps onto any run left in
`queued`/`running`).

## Legacy topic-pipeline tables — orphaned, not dead

These three tables are still in the schema and still seeded/cleaned on
startup, but **no route reads or writes them anymore**. `6444f36` removed
`api/routes/words.py` and `api/routes/topics.py` (0 callers left after
`js/app.js`/`js/editor.js` were deleted) along with `words_repo.py`,
`grammar_parser.py`, `wiktionary_client.py` and `topic_pack_service.py`. The
dictionary product now runs entirely on `vocab_cards` below.

### `words`
Old Postgres vocabulary table (predates the SQLite/Mistral pipeline in
`app/vocab/`).

| Column | Notes |
|--------|-------|
| `german` | Lemma, no article prefix |
| `article` | der/die/das or null |
| `word_type` | noun, verb, adj, … |
| `translation_ru` | Russian gloss |
| `level` | B1/B2/C1 |
| `grammar_data` | JSON, nullable |
| `examples` | JSON array |
| `source` | `"seed"` for every row today — `ensure_seed_data` in `app/db/init_data.py` inserts exactly 3 rows (`Technologie`, `Fortschritt`, `Digitalisierung`) when the table is empty; nothing else writes into it outside tests |

Still touched at container startup by `app/services/word_cleanup.py`
(idempotent lemma/dedup fixes left over from the old pipeline), which is why
the table isn't simply gone.

### `word_topics`
M2M: word ↔ topic string. Unique on `(word_id, topic)`. Same fate as `words` —
populated only by seed data, read only by the startup cleanup pass.

### `user_word_progress`
Per-user score/streak per `Word`. Unique on `(user_id, word_id)`. No code path
constructs a row outside `backend/tests/` — a repo-wide search for
`UserWordProgress(` finds only the model definition and two test files.
`app/services/user_stats_service.count_learned_words` still queries it (used
by `record_activity`, called from essay analysis), so `user_stats.total_words_learned`
is always `0` in practice: the table it counts from is never populated.

## Essay clichés

### `phrases`
Redemittel / essay clichés (Wortschatz für den Aufbau eines Aufsatzes), served
by `GET /api/phrases/templates`.

| Column | Notes |
|--------|-------|
| `text_de` | Phrase text (contains a template gap as `...` for most rows) |
| `translation_ru` | Russian translation, may be empty |
| `essay_part` | `einleitung`, `argument`, `gegenargument`, `beispiel`, `schluss`, … |
| `topic` | nullable; `list_templates` falls back to untagged rows when no topic matches |
| `level` | B1/B2/C1 |

`ensure_seed_data` inserts 3 seed rows if the table is empty, one of them with
`essay_part="argument1"` — a typo baked into the seed data itself (grep
`init_data.py`), separate from the production data grown by hand afterwards.

### `user_phrase_known`
Per-user known/unknown flag on a `phrase`. Unique on `(user_id, phrase_id)`.
Written by `POST /api/phrases/{phrase_id}/known`.

### `user_stats`
One row per user: `streak_current`, `streak_last_date` (Europe/Berlin
calendar day, see `app/services/user_stats_service.py`), `total_words_learned`
(see caveat above — currently always 0). Updated by `record_activity`, called
after every essay analysis run.

## Wörterbuch — dictionary mirror + personal word list

The enrichment worker owns `enrichment.db` (SQLite) and writes to it around
the clock; it must not be disturbed. Fuzzy search (`pg_trgm`) and the personal
word list need to be queryable together, so finished cards are copied
(never written back) into Postgres by `app/vocab/mirror.py`. Full comment
trail: `backend/app/db/models.py`, from the `VocabCard` class onward.

### `vocab_cards`
One row per headword. Primary key is the lemma itself (`lemma`, not a
surrogate id) — `enrichment.db` doesn't have one either.

| Column | Notes |
|--------|-------|
| `lemma` | PK, case-sensitive on purpose (`Morgen` vs `morgen` are different rows) |
| `lemma_norm` / `lemma_ascii` | Two case-folded search keys: `lemma_norm` substitutes umlauts correctly (grün→gruen), `lemma_ascii` flattens them (grün→grun); both carry a GIN trigram index because neither form alone finds every query typed on an umlaut-less keyboard |
| `level` | raw CEFR-ish value from the source, including `unlisted` |
| `band` | display value clamped to B1/B2/C1 — the key the frontend brush map (`WASH` in `js/words-data.js`) indexes by. Kept separate from `freq` (corpus frequency, computed in `norm.py`) on purpose: frequency was measured to be a bad proxy for CEFR level (see `info/PLANS.md`), so the two are different columns and different claims |
| `zipf` | wordfreq frequency, nullable; used as a ranking tie-break so common words don't lose to rarer ones with the same match score |
| `form_kind` / `form_of` | non-null when the source dictionary listed this lemma as an inflected form / compound-part / abbreviation / variant rather than a headword (`app/vocab/forms.py`); search demotes these at equal match quality instead of hiding them |
| `morphology` | full inflection paradigm imported from a Wiktionary dump (`app/vocab/morph.py`), `null` for lemmas Wiktionary doesn't have. Declared with `JSON(none_as_null=True)` **deliberately, not for style**: a plain JSON column serializes Python `None` as the JSON scalar `null`, which is not SQL `NULL` — the model's own comment records that the first resync wrote `'null'::jsonb` into 27 929 rows, which made `morphology IS NOT NULL` count all of them as "has a paradigm" |
| `source_created_at` | watermark copied from `enrichment.db`'s `cards.created_at`; the incremental mirror cursor |

Indexes are declared in `__table_args__` on the model itself (not only in a
migration) for the reason spelled out in the header note above.

### `vocab_card_translations`
One row per Russian meaning (`ru_all` in the source), FK'd to `vocab_cards.lemma`
with `ondelete="CASCADE"`. Kept as separate rows instead of one concatenated
string because trigram similarity scores well against a single meaning and
badly against a long concatenation — this is what makes RU→DE search work.

### `user_word_list`
A word the user put on their personal learning list.

> Keyed by `lemma` as plain text **on purpose — no FK to `vocab_cards`**: the
> enrichment prompt already separates homographs by case (`Morgen`/`morgen`,
> `Essen`/`essen`), so a lemma is unambiguous on its own, and a future
> browser extension is expected to add words straight off arbitrary pages that
> may not be in the dictionary (yet) — see the model's own docstring, and
> `info/CRITICAL-LINKS.md` §6b for the fuller story.

Snapshot columns (`ru`, `level`, `band`, `pos`, `article`, `topic`) duplicate
enough of the card to render the list in one query without joining
`vocab_cards`; they are written on add and can lag behind a re-enrichment.
There is no `definition_de`/`grammar`/`examples` here — opening a card from the
list still goes through `GET /api/vocab/entry/{lemma}`. Unique on
`(user_id, lemma)`.

## Conventions

- Primary keys are `Mapped[int]`, i.e. Postgres `integer` (32-bit) — nothing
  in this schema uses `bigint`. `app/api/params.py` bounds path parameters to
  `2**31 - 1` for exactly this reason (a bigger number reaching the DB driver
  used to raise a raw 500 instead of a clean 422; see that module's own
  docstring).
- `vocab_cards` / `vocab_card_translations` / `user_word_list` are the live
  dictionary product; `words` / `word_topics` / `user_word_progress` are the
  table shapes it replaced and are kept around only because startup cleanup
  and old tests still touch them — treat them as historical, not as a second
  vocabulary source.
- `words.grammar_data` was meant to be validated against a schema that lived
  in `grammar_schema.py`; that file no longer exists in the repo (removed with
  the rest of `backend/app/pipeline/`, commit `039c585`) — there is nothing
  left in the codebase to enforce it against.
