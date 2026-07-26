# Vocab pipeline

**Проверено против кода: 2026-07-26.** Этот файл раньше описывал topic-pipeline
(`runner.py`, `discovery.py`, `extraction.py`, `enrichment.py`, `supplement.py`,
`scheduler.py`, `/api/pipeline/*`) — ни одного из этих файлов и роутов в
репозитории больше нет (`ls backend/app/pipeline/` → *no such file or
directory*). Переписан с нуля про реальный конвейер, который живёт целиком в
[`backend/app/vocab/`](../backend/app/vocab/) и питает `index.html` +
`pipeline.html`.

## One-paragraph summary

Two independent stages, two SQLite files, one Postgres mirror:

1. **Deterministic build (no LLM).** Bilingual dictionary dumps (offline,
   outside the repo) → [`build.py`](../backend/app/vocab/build.py) → `vocab.db`
   (`words` table). Driven from `pipeline.html` (`js/pipeline.js`), admin-only.
2. **LLM enrichment.** A background worker per authenticated account, each
   using *that account's own* Mistral key, claims words from `vocab.db` and
   writes validated cards to `enrichment.db` (`cards` + `word_status`). Driven
   from `pipeline.html` (`js/enrich.js`).
3. **Mirror.** [`mirror.py`](../backend/app/vocab/mirror.py) copies finished
   cards from `enrichment.db` into Postgres (`vocab_cards`,
   `vocab_card_translations`) — read-only source, incremental cursor, runs on
   a timer plus at every worker start.
4. **Search.** [`search.py`](../backend/app/vocab/search.py) queries the
   Postgres mirror with `pg_trgm`. This is what `index.html`
   (`js/wb-page.js` → `GET /api/vocab/search` / `entry/{lemma}`) actually reads
   — never SQLite directly.

```
dictionaries/ (host, git-ignored, mounted read-only)
       │  DICT_ROOT
       ▼
backend/app/vocab/build.py  ──(wordfreq + goethe.py CEFR)──▶  vocab.db "words"
       ▲                                                          │
       │ backend/scripts/import_new_words.py (offline, Wiktionary)│ VOCAB_DB
       │                                                          ▼
       │                                        app/vocab/enrich.py + enrich_worker.py
       │                                        (claim → Mistral, per-account key)
       │                                                          │
       │  backend/scripts/import_morphology.py (offline, paradigms) │ ENRICH_DB
       │                                                          ▼
       └───────────────────────────────────  enrichment.db "cards" + "word_status"
                                                                  │
                                                app/vocab/mirror.py (read-only,
                                                incremental, SQLite → Postgres)
                                                                  ▼
                                      Postgres: vocab_cards, vocab_card_translations
                                                                  │
                                                    app/vocab/search.py (pg_trgm)
                                                                  ▼
                                    GET /api/vocab/search, /api/vocab/entry/{lemma}
                                                                  ▼
                                                index.html (js/wb-page.js, wb-card.js)
```

## Stage 1 — deterministic build (`vocab.db`, no model calls)

| Module | Role |
|--------|------|
| [`sources.py`](../backend/app/vocab/sources.py) | Registry of which dictionaries to ingest (general De-Ru + synonyms/collocations/idioms); `DICT_ROOT` env picks the folder |
| [`readers.py`](../backend/app/vocab/readers.py) | Unified reader over DSL/StarDict/MDX, yields `(lemma, contribution)` |
| [`dsl.py`](../backend/app/vocab/dsl.py) | Dependency-free ABBYY Lingvo DSL reader (UTF-16LE/UTF-8-BOM, `.dsl.dz`) |
| [`goethe.py`](../backend/app/vocab/goethe.py) | CEFR level from the official Goethe/ÖSD A1–B1 wordlist + a supplemental A1–C2 list — **not** from frequency rank (frequency is a bad CEFR proxy: `Doppelzimmer` is A1 but corpus-rare) |
| [`build.py`](../backend/app/vocab/build.py) | Orchestrates the above, ranks with `wordfreq`, writes `vocab.db`. Callable as a background job (`run_build(progress=...)`) or CLI |
| [`store.py`](../backend/app/vocab/store.py) | Read-only helpers over `vocab.db` for the dashboard (`search`, `get`, `stats`) |
| [`demo_raw.py`](../backend/app/vocab/demo_raw.py), [`show.py`](../backend/app/vocab/show.py) | CLI inspection tools — raw per-dictionary contribution and per-word "touch the real result" view |

**Dictionaries live outside the repo.** `dictionaries/` is git-ignored; in
Docker it is bind-mounted read-only from the host (`docker-compose.yml`:
`./dictionaries:/app/dictionaries:ro`, `DICT_ROOT=/app/dictionaries`).
`sources.py`'s hardcoded fallback path is a dev-machine default and is not the
one used inside the container.

**Route:** `POST /api/vocab/build?min_zipf=` (`require_admin` — it deletes and
rebuilds `vocab.db` from scratch), `GET /api/vocab/{status,stats,words,
word/{lemma}}` (public reads). See `info/backend-api.md`.

⚠️ `VOCAB_DB`'s default path (no env var set) resolves to an empty stub
`app/vocab/vocab.db` next to the real, mounted database — see
`info/CRITICAL-LINKS.md` §6a and `vocab-db-default-path-is-a-stub` in project
memory.

## Stage 2 — enrichment (`enrichment.db`, Mistral)

| Module | Role |
|--------|------|
| [`enrich.py`](../backend/app/vocab/enrich.py) | Format + storage: opens `vocab.db` read-only (ATTACH) as the input, owns `enrichment.db`'s `word_status` (per-lemma lease/attempts/phase) and `cards` (validated output + provenance). `PROMPT_VERSION` gates re-enrichment of stale cards |
| [`enrich_worker.py`](../backend/app/vocab/enrich_worker.py) | One daemon thread per authenticated account; claims disjoint batches, calls Mistral through `app/services/mistral_http.py` with that account's decrypted key |
| [`funcwords.py`](../backend/app/vocab/funcwords.py) | ~25 hand-written cards (`model='handwritten'`, zero tokens) for the closed class the model refuses by design — articles (`der/die/den/dem/des`), contracted prepositions (`im/am/zum/...`) |
| [`forms.py`](../backend/app/vocab/forms.py) | Tags dictionary-listed word forms (`form_kind`/`form_of`) so search can rank a real headword above its inflected form without deleting the form's card |
| [`morph.py`](../backend/app/vocab/morph.py) | Joins full inflection paradigms from a German Wiktionary dump onto existing cards — pure join, no model calls |
| [`norm.py`](../backend/app/vocab/norm.py) | Shared normalization (folded lemma, CEFR→band clamp, POS→type, zipf→freq label) used by the mirror, search and word list alike |

**Phases (`enrich.PHASES`, in `enrich.py`).** A phase is a tag on
`word_status.phase`, not a coordinator — `claim` simply serves whichever
tagged phase still has work, so N accounts converge without leader election:

| # | phase | seeded by |
|---|-------|-----------|
| 1 | `repair_pairs` | `plan_repairs()`, runs once per process at first worker start |
| 2 | `repair_case` | `plan_repairs()` |
| 3 | `repair_ortho` | `plan_repairs()` |
| 4 | `repair_split` | `plan_repairs()` |
| 5 | `repair_qa` | **not** `plan_repairs()` — tagged by the offline `backend/scripts/qa_cards.py --requeue --apply`, which also sets `drop_card=True` (deletes the card immediately, unlike phases 1–4 which keep the old card until the replacement lands) |
| 6 | `backfill` | default phase for any untagged word |

**Route:** `POST /api/vocab/enrich/start` (`require_user`, uses the caller's
own key), `POST /api/vocab/enrich/stop`, `GET /api/vocab/enrich/{progress,
cards,card/{lemma},status}`, `POST /api/vocab/enrich/requeue` (scope-gated, see
`info/backend-api.md`), admin-only fleet control
`/api/vocab/enrich/fleet{,/start,/stop}` (starts/stops a worker on *every*
account that has a key attached — spends other accounts' Mistral quota, hence
admin-gated). Full field-by-field detail (skip rules, orthography-1996
renames, case-fold matching) is in `info/CRITICAL-LINKS.md` §6a — not repeated
here to avoid two copies drifting.

## Stage 3 — mirror (`enrichment.db` → Postgres)

[`mirror.py`](../backend/app/vocab/mirror.py): SQLite is opened read-only and
never written back to. Cursor is `(created_at, lemma)`; `save_cards` uses
`INSERT OR REPLACE` with a fresh `created_at`, so a re-enriched card rides the
same forward cursor as a brand-new one. `periodic_sync()` is started as an
asyncio task in `app/main.py`'s `on_startup` and re-runs every `SYNC_INTERVAL`
(300 s); `POST /api/vocab/mirror/sync` (`require_admin`) forces an immediate
pass. `full_resync()` replays everything from `(0.0, "")` — needed after an
in-place column backfill that doesn't move `created_at` (e.g. `plan_repairs()`
filling `cards.zipf`).

## Stage 4 — search (Postgres, `pg_trgm`)

[`search.py`](../backend/app/vocab/search.py): Latin input searches the German
lemma (`lemma_norm`/`lemma_ascii`), Cyrillic searches `ru_all`. No LLM call —
this resolves words already in the base, and says so honestly when one is
missing rather than inventing it. `MAX_LIMIT = 50` per query, prefix-only below
`MIN_TRIGRAM_CHARS = 3`. Ranking constants (`_EXACT = 2.0`, `_PREFIX = 1.0`,
tie-breaks) and their history are documented in `info/CRITICAL-LINKS.md` §6b.

## Offline maintenance scripts (`backend/scripts/`, NOT in Docker CMD)

| Script | Role |
|--------|------|
| `import_new_words.py` | Appends new headwords from a Wiktionary dump into `vocab.db` (`--dry-run`, `--min-zipf`, `--limit`, `--backup`) — the intake side of [`intake.py`](../backend/app/vocab/intake.py) |
| `import_morphology.py` | Joins Wiktionary inflection paradigms onto `enrichment.db` cards (`morph.py`) — **must** be run with an explicit `--enrich-db`, and again after every intake, since paradigms don't reach new cards on their own |
| `qa_cards.py` | Mechanical + model-assisted QA pass over enriched cards; `--requeue --apply` is what tags the `repair_qa` phase |
| `coverage.py` | Measures dictionary coverage against an external text corpus (not the base itself) |
| `bench_vocab_batch.py` | Throughput/latency bench for enrichment batch size |
| `cleanup_db.py` | Ad-hoc SQLite maintenance |

These are explicitly out of scope for automated tooling per `CLAUDE.md` — not
run by CI, not run by an agent without an explicit request.

## DB tables

- **SQLite `vocab.db`** (`words`) — raw dictionary dump, immutable except for
  full rebuilds by `build.py` and the intake script's appends.
- **SQLite `enrichment.db`** (`word_status`, `cards`, `token_usage`) — worker
  state, the enriched output, and per-account Mistral spend.
- **Postgres** (`app/db/models.py`): `vocab_cards`, `vocab_card_translations`
  (the mirror — derived, safe to drop and rebuild in ~15 s via
  `full_resync()`), `user_word_list` (real user data, **not** derived).

## Config

| Setting | Where | Default |
|---------|-------|---------|
| `VOCAB_DB` | env | `backend/app/vocab/vocab.db` (a stub — see warning above); Docker sets `/app/vocab_data/vocab.db` |
| `ENRICH_DB` | env | `VOCAB_DB`'s directory, `enrichment.db` |
| `DICT_ROOT` | env | dev-machine path in `sources.py`; Docker sets `/app/dictionaries` |
| `ADMIN_EMAILS` | `backend/.env` / `Settings.admin_emails` | empty (no admins) |
| `MISTRAL_KEY_SECRET` | `backend/.env` / `Settings.mistral_key_secret` | empty → per-user key storage disabled |
| `mistral_model` | `Settings.mistral_model` | `mistral-large-latest` |

There is no `pipeline_*` setting left in `backend/app/config.py` — the whole
`pipeline_target_words`/`pipeline_batch_size`/`pipeline_stale_run_minutes`
family belonged to the removed topic-pipeline.

## Topics

[`topics.py`](../backend/app/vocab/topics.py): 147 topics across 18 macro-areas
(mixing thematic areas with notional/functional ones like time, quantity,
cause/effect, so function words have a topic home too). Each enriched card gets
1..N topics attached during enrichment; there is no separate topic-import
route — the old `/api/topics/{slug}/import` and its YAML files are gone along
with the topic-pipeline.
