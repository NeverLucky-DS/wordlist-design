# Technical Debt & Unused Files Audit

> **Project:** [wordlist-design](.) (Deutsch Essay Trainer)  
> **Date:** 2026-07-03  
> **Author:** Cursor agent audit  
> **Scope:** Full repository — production app, backend, design system, migration stubs  
> **Method:** Static analysis — file tree, grep for references, import graph, pytest collection, `docker-compose.yml` mount inspection, MD5 comparison of overlapping asset names (reported by subagent)  
> **Status:** Report only — no code changes made

---

## How to read this document

### Confidence scale

| Level | Meaning |
|-------|---------|
| **🟢 High (90–100%)** | Verified by grep/import analysis, file listing, or direct command (`pytest --collect-only`, `docker-compose` volumes). Safe to act on. |
| **🟡 Medium (60–89%)** | Strong evidence but not runtime-tested; may have dynamic/indirect references; or comparison done on filename overlap only. |
| **🔴 Low (30–59%)** | Architectural judgment or inferred from docs; needs human confirmation before deletion/refactor. |

### Link conventions

- Paths are relative to repo root: [`backend/app/main.py`](backend/app/main.py)
- Line references use code blocks where helpful
- **Prod** = mounted in [`docker-compose.yml`](docker-compose.yml) and served by nginx :8753 or uvicorn :8000

---

## Executive summary

| Category | Severity | Confidence |
|----------|----------|------------|
| Unused/orphan files (explicit list) | Medium | 🟢 High |
| Semantic asset duplication (`worte/` vs DS brushes, `images/` vs DS images) | High | 🟡 Medium (MD5 via subagent; filenames verified) |
| Parallel UI implementations (vanilla / DS React / editor-extract) | High | 🟢 High |
| Pipeline v2 (production) vs v3 (scripts only) | Critical | 🟢 High |
| Missing Alembic migrations | High | 🟢 High |
| Test coverage gaps in pipeline I/O | Medium | 🟢 High |
| Outdated documentation | Low–Medium | 🟢 High |
| Design System folder not in production | Informational | 🟢 High |

**Bottom line:** The repo is functional but carries **structural debt from parallel development tracks**. The highest-risk debt is not stray PNGs — it is **two pipeline write paths** and **duplicated asset trees that have already diverged in bytes**.

---

## 1. Production architecture (what actually runs)

### 1.1 Deployed stack

| Layer | Path | In Docker? | Confidence |
|-------|------|------------|------------|
| Wörterbuch | [`index.html`](index.html), [`js/app.js`](js/app.js), [`css/styles.css`](css/styles.css) | ✅ | 🟢 High |
| Essay editor | [`editor.html`](editor.html), [`js/editor.js`](js/editor.js), [`css/editor.css`](css/editor.css) | ✅ | 🟢 High |
| Pipeline dashboard | [`pipeline.html`](pipeline.html), [`css/pipeline.css`](css/pipeline.css), inline `<script>` | ✅ | 🟢 High |
| Static assets | [`images/`](images/), [`worte/`](worte/) | ✅ | 🟢 High |
| Shared chrome | [`js/site-header.js`](js/site-header.js), [`css/site-header.css`](css/site-header.css) | ✅ | 🟢 High |
| Backend API | [`backend/app/`](backend/app/) | ✅ :8000 | 🟢 High |
| PostgreSQL | `docker-compose.yml` service `postgres` | ✅ | 🟢 High |

Evidence: [`docker-compose.yml`](docker-compose.yml) lines 42–50 mount only `index.html`, `editor.html`, `pipeline.html`, `css/`, `js/`, `images/`, `worte/`.

### 1.2 Not deployed (reference / future / docs)

| Path | Size (approx.) | Purpose | Confidence |
|------|----------------|---------|------------|
| [`Deutsch Essay Design System/`](Deutsch%20Essay%20Design%20System/) | ~65 MB | Design system gallery, tokens, component cards, UI kit prototypes | 🟢 High |
| [`editor-extract/`](editor-extract/) | ~296 KB | Future React+TipTap editor migration stub | 🟢 High |
| [`screenshots/`](screenshots/) | ~1.4 MB | README documentation images | 🟢 High |
| [`word-card.html`](word-card.html) | — | Standalone UI mock | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md), [`README.md`](README.md) | — | Documentation | 🟢 High |

### 1.3 HTML entry points (27 total)

| Group | Count | Files | Confidence |
|-------|-------|-------|------------|
| Production | 3 | `index.html`, `editor.html`, `pipeline.html` | 🟢 High |
| Orphan mock | 1 | `word-card.html` | 🟢 High |
| Design System component cards | 6 | `Deutsch Essay Design System/components/*/*.card.html` | 🟢 High |
| Design System guidelines | 15 | `Deutsch Essay Design System/guidelines/*.html` | 🟢 High |
| Design System UI kits | 2 | `ui_kits/editor/index.html`, `ui_kits/woerterbuch/index.html` | 🟢 High |

---

## 2. Unused and orphan files

### 2.1 Safe deletion candidates (no production dependency)

| File | Evidence | Confidence | Recommended action |
|------|----------|------------|-------------------|
| [`word-card.html`](word-card.html) | No inbound links (`rg word-card` → only comments in `js/editor.js`). Not in compose. Uses Playfair Display; prod uses Cormorant+Inter. | 🟢 High | Delete or move to `archive/` |
| [`screenshots/Deutsch_2.png`](screenshots/Deutsch_2.png) | No references in README, HTML, CSS, JS | 🟢 High | Delete |
| [`Deutsch Essay Design System/deutsch-essay-editor.pptx`](Deutsch%20Essay%20Design%20System/deutsch-essay-editor.pptx) | No references in repo | 🟢 High | Delete or keep outside git |
| [`Deutsch Essay Design System/assets/images/botanical-top.png`](Deutsch%20Essay%20Design%20System/assets/images/botanical-top.png) | `rg botanical-top` → no matches | 🟢 High | Delete (DS-only orphan) |
| [`Deutsch Essay Design System/assets/images/decor-foot.png`](Deutsch%20Essay%20Design%20System/assets/images/decor-foot.png) | `rg decor-foot` → no matches | 🟢 High | Delete (DS-only orphan) |
| [`Deutsch Essay Design System/assets/images/wash-orange.png`](Deutsch%20Essay%20Design%20System/assets/images/wash-orange.png) | `rg wash-orange` → no matches | 🟢 High | Delete (DS-only orphan) |
| [`Deutsch Essay Design System/assets/images/autumn.png`](Deutsch%20Essay%20Design%20System/assets/images/autumn.png) | Prod uses [`images/autumn.png`](images/autumn.png) via [`js/editor.js`](js/editor.js); DS copy unreferenced | 🟢 High | Delete DS copy |

### 2.2 Intentionally kept but not in production runtime

| Path | Evidence | Confidence | Notes |
|------|----------|------------|-------|
| [`editor-extract/`](editor-extract/) | Documented in [`editor-extract/README.md`](editor-extract/README.md) as future migration. No `package.json`. Not in compose. | 🟢 High | Incomplete — expects missing webp assets (see §2.3) |
| [`backend/scripts/cleanup_db.py`](backend/scripts/cleanup_db.py) | Manual CLI only; not imported by `app/` | 🟢 High | Dev/maintenance tool |
| [`backend/scripts/backfill_grammar.py`](backend/scripts/backfill_grammar.py) | Used by `reprocess_topic.py`; not in API/scheduler | 🟢 High | Dev/maintenance tool |
| [`backend/scripts/reprocess_topic.py`](backend/scripts/reprocess_topic.py) | Alternate v3 pipeline path; not in API | 🟢 High | Dev/maintenance tool |
| [`backend/audit_db.py`](backend/audit_db.py) | Standalone; no `app.*` imports | 🟢 High | Dev/maintenance tool |
| Entire [`Deutsch Essay Design System/`](Deutsch%20Essay%20Design%20System/) | Design reference; 23 HTML gallery pages | 🟢 High | Keep if DS is active; archive if not |

### 2.3 Missing assets referenced by editor-extract

| Expected path | Referenced in | Exists in repo? | Confidence |
|---------------|---------------|-----------------|------------|
| `/assets/wordlist/brushes/*.webp` | `editor-extract/frontend/src/.../brushAssets.ts` | ❌ (only [`worte/*.png`](worte/)) | 🟡 Medium |
| `/assets/wordlist/decor/*.webp` | editor-extract CSS/TS | ❌ | 🟡 Medium |
| `/assets/editorial/analyse-cta.png` | `EditorStatusBar.tsx` | ❌ | 🟡 Medium |
| `/assets/editorial/annotation-note-bg.webp` | `editorial.css` | ❌ | 🟡 Medium |
| `/assets/editorial/sidebar-decor.png` | `constants.ts` (defined, usage unclear) | ❌ | 🔴 Low |

### 2.4 Production assets — all referenced ✅

| Folder | Files | Referenced by | Confidence |
|--------|-------|---------------|------------|
| [`images/`](images/) | 8 PNG | [`css/styles.css`](css/styles.css), [`css/editor.css`](css/editor.css), [`css/pipeline.css`](css/pipeline.css), [`js/editor.js`](js/editor.js) | 🟢 High |
| [`worte/`](worte/) | 15 PNG | `WASH` map in [`js/app.js`](js/app.js), [`js/editor.js`](js/editor.js) | 🟢 High |

---

## 3. Duplication

### 3.1 Asset duplication (semantic twins, different bytes)

| Pair | Overlap | Byte-identical? | Prod canonical | Confidence |
|------|---------|-----------------|----------------|------------|
| [`worte/`](worte/) ↔ [`Deutsch Essay Design System/assets/brushes/`](Deutsch%20Essay%20Design%20System/assets/brushes/) | 15 same filenames | **No** (all differ) | `worte/` | 🟡 Medium |
| [`images/`](images/) ↔ [`Deutsch Essay Design System/assets/images/`](Deutsch%20Essay%20Design%20System/assets/images/) | 5 shared names | **No** | `images/` | 🟡 Medium |
| [`screenshots/`](screenshots/) ↔ [`Deutsch Essay Design System/screenshots/`](Deutsch%20Essay%20Design%20System/screenshots/) | `Deutsch_3`–`Deutsch_8` | **No** | Root `screenshots/` (README) | 🟡 Medium |

**Risk:** Editing brushes in one tree does not update the other. Design has already diverged.

**Root-only images:** `kli-1.png`, `kli-2.png`, `kli-3.png` — used in [`css/editor.css`](css/editor.css) / [`js/editor.js`](js/editor.js). Confidence: 🟢 High.

**DS-only images (besides orphans in §2.1):** `paper-texture.png` — used only in [`Deutsch Essay Design System/guidelines/brand-decor.html`](Deutsch%20Essay%20Design%20System/guidelines/brand-decor.html). Confidence: 🟢 High.

### 3.2 Code duplication (functional parallels)

| Concern | Production | Parallel | Confidence |
|---------|------------|----------|------------|
| Wörterbuch UI | [`js/app.js`](js/app.js) (834 lines) | [`Deutsch Essay Design System/ui_kits/woerterbuch/Woerterbuch.jsx`](Deutsch%20Essay%20Design%20System/ui_kits/woerterbuch/Woerterbuch.jsx) | 🟢 High |
| Essay editor | [`editor.html`](editor.html) + [`js/editor.js`](js/editor.js) (1593 lines) | [`editor-extract/frontend/src/editor/`](editor-extract/frontend/src/editor/) (27 files) | 🟢 High |
| Styles | [`css/styles.css`](css/styles.css) | [`Deutsch Essay Design System/styles.css`](Deutsch%20Essay%20Design%20System/styles.css) + [`tokens/`](Deutsch%20Essay%20Design%20System/tokens/) | 🟢 High |
| Backend | [`backend/`](backend/) | ~~`editor-extract/backend/`~~ **removed** ✅ | 🟢 High |

### 3.3 Backend service duplication

| Concern | Implementations | Files | Confidence |
|---------|-----------------|-------|------------|
| Wiktionary fetch | MediaWiki parse API | [`backend/app/pipeline/enrichment.py`](backend/app/pipeline/enrichment.py) | 🟢 High |
| | REST API | [`backend/app/services/wiktionary_client.py`](backend/app/services/wiktionary_client.py) | 🟢 High |
| | Batch fetch (scripts) | [`backend/scripts/backfill_grammar.py`](backend/scripts/backfill_grammar.py) → [`wiktionary_grammar.py`](backend/app/pipeline/wiktionary_grammar.py) | 🟢 High |
| Mistral HTTP | Pipeline (429 cooldown, retry) | [`backend/app/pipeline/mistral_http.py`](backend/app/pipeline/mistral_http.py) | 🟢 High |
| | Essays (httpx, no shared retry) | [`backend/app/services/mistral_analyzer.py`](backend/app/services/mistral_analyzer.py) | 🟢 High |
| HTTP libraries | `requests` + `httpx` both in [`requirements.txt`](backend/requirements.txt) | — | 🟢 High |

---

## 4. Backend technical debt

### 4.1 Pipeline generations (CRITICAL)

| Generation | Modules | Used by | Confidence |
|------------|---------|---------|------------|
| **v2 (production)** | [`discovery.py`](backend/app/pipeline/discovery.py), [`extraction.py`](backend/app/pipeline/extraction.py), [`enrichment.py`](backend/app/pipeline/enrichment.py), [`supplement.py`](backend/app/pipeline/supplement.py), [`normalize.py`](backend/app/pipeline/normalize.py), [`runner.py`](backend/app/pipeline/runner.py), [`scheduler.py`](backend/app/pipeline/scheduler.py) | API [`/api/pipeline/*`](backend/app/api/routes/pipeline.py), background scheduler | 🟢 High |
| **v3 (scripts only)** | [`wiktionary_grammar.py`](backend/app/pipeline/wiktionary_grammar.py), [`content_llm.py`](backend/app/pipeline/content_llm.py), [`verify.py`](backend/app/pipeline/verify.py), [`grammar_schema.py`](backend/app/pipeline/grammar_schema.py) | [`scripts/reprocess_topic.py`](backend/scripts/reprocess_topic.py), [`scripts/backfill_grammar.py`](backend/scripts/backfill_grammar.py) only | 🟢 High |

**Impact:** Words written via production runner vs maintenance scripts may have **different `grammar_data` shape and quality**. Confidence: 🟡 Medium (inferred from code paths; not validated on live DB).

**`normalize_grammar_data()`** in [`grammar_schema.py`](backend/app/pipeline/grammar_schema.py) is **never called on writes** from [`runner.py`](backend/app/pipeline/runner.py). Confidence: 🟢 High.

### 4.2 Database & schema management

| Issue | Evidence | Confidence |
|-------|----------|------------|
| Alembic in deps, no migrations | [`alembic>=1.14.0`](backend/requirements.txt); no `alembic/` directory | 🟢 High |
| Schema via `create_all` + manual ALTER | [`backend/app/main.py`](backend/app/main.py) `_ensure_new_columns` — only `phrases_added`, `target_words` on `pipeline_runs` | 🟢 High |
| Topic casing inconsistency | `runner.py` lowercases; [`pipeline.py`](backend/app/api/routes/pipeline.py) `/run` and `/queue` preserve input case | 🟢 High |
| Topic packs path missing | `data/topics/*.topic.yaml` does not exist; [`topic_pack_service.py`](backend/app/services/topic_pack_service.py) defaults `TOPICS_DIR=/data/topics` (not mounted in compose) | 🟢 High |

### 4.3 Dead code (backend)

| Symbol | File | Callers | Confidence |
|--------|------|---------|------------|
| `_DDG_QUERIES` | [`discovery.py`](backend/app/pipeline/discovery.py) L37 | None (dynamic queries used instead) | 🟢 High |
| `enrich_word()` | [`enrichment.py`](backend/app/pipeline/enrichment.py) L368 | None | 🟢 High |
| `normalize_grammar_data()` | [`grammar_schema.py`](backend/app/pipeline/grammar_schema.py) L161 | None in `app/` | 🟢 High |
| `psycopg2-binary` | [`requirements.txt`](backend/requirements.txt) | Only [`audit_db.py`](backend/audit_db.py) | 🟢 High |

### 4.4 Error handling & ops gaps

| Issue | Location | Confidence |
|-------|----------|------------|
| Scheduler broad `except` may leave queue ambiguous | [`scheduler.py`](backend/app/pipeline/scheduler.py) | 🟡 Medium |
| Pipeline runs in `BackgroundTasks` — no process isolation | [`pipeline.py`](backend/app/api/routes/pipeline.py) | 🟢 High |
| Essay Mistral lacks 429/cooldown of pipeline | [`mistral_analyzer.py`](backend/app/services/mistral_analyzer.py) | 🟢 High |
| `/health` always `{"status":"ok"}` — no DB/scheduler check | [`health.py`](backend/app/api/routes/health.py) | 🟢 High |
| `datetime.utcnow()` throughout | `runner.py`, `scheduler.py`, `types.py` | 🟢 High |
| Deprecated `@app.on_event("startup")` | [`main.py`](backend/app/main.py) | 🟢 High |
| v1 legacy cleanup on every startup | [`main.py`](backend/app/main.py) L69–85, [`topic_pack_service.py`](backend/app/services/topic_pack_service.py) | 🟢 High |

### 4.5 Startup duplicate cleanup

[`main.py`](backend/app/main.py) runs `fix_word_lemmas` + `dedupe_words_by_german` on startup.  
[`topic_pack_service.import_topic_pack`](backend/app/services/topic_pack_service.py) runs the same again.  
Confidence: 🟢 High.

### 4.6 Test coverage

**Collected:** 36 tests (`pytest --collect-only`). README claims "pytest (16)" — **stale**. Confidence: 🟢 High.

| Well covered | Under-tested / not tested | Confidence |
|--------------|---------------------------|------------|
| API routes (mocked) | [`discovery.py`](backend/app/pipeline/discovery.py) — Grok + DDG | 🟢 High |
| [`normalize.py`](backend/app/pipeline/normalize.py) | [`enrichment.py`](backend/app/pipeline/enrichment.py) — Wiktionary/DWDS/Mistral | 🟢 High |
| [`mistral_http.py`](backend/app/pipeline/mistral_http.py) | [`extraction.py`](backend/app/pipeline/extraction.py) | 🟢 High |
| Scheduler/autonomy (mocked) | [`supplement.py`](backend/app/pipeline/supplement.py), [`topics_catalog.py`](backend/app/pipeline/topics_catalog.py) | 🟢 High |
| Pipeline control loop (mocked) | v3 modules, [`topic_pack_service.py`](backend/app/services/topic_pack_service.py) | 🟢 High |
| | PostgreSQL integration (tests use SQLite only) | 🟢 High |

Test files: [`backend/tests/`](backend/tests/).

---

## 5. Frontend technical debt

| Issue | Location | Lines / detail | Confidence |
|-------|----------|----------------|------------|
| Monolithic editor | [`js/editor.js`](js/editor.js) | ~1593 lines — dictionary, editor, popover, API | 🟢 High |
| Inline dashboard logic | [`pipeline.html`](pipeline.html) | ~350 lines inline `<script>`, no `js/pipeline.js` | 🟢 High |
| Manual cache busting | All prod HTML | `?v=N` query params on CSS/JS | 🟢 High |
| Nav placeholder links | `index.html`, `editor.html`, `pipeline.html` | `href="#"` on Dashboard, Lernen, etc. | 🟢 High |
| nginx aggressive cache | [`nginx.conf`](nginx.conf) L9–11 | 7d `immutable` on static assets — OK if `?v=` bumped | 🟢 High |
| No bundler/linter/TS | `js/` | Intentional vanilla stack | 🟢 High |

### Frontend file map (production)

| File | Role | Referenced by |
|------|------|---------------|
| [`js/app.js`](js/app.js) | Wörterbuch logic, WASH brushes | [`index.html`](index.html) |
| [`js/editor.js`](js/editor.js) | Essay editor + word panel | [`editor.html`](editor.html) |
| [`js/editor-api.js`](js/editor-api.js) | Backend bridge | [`editor.html`](editor.html) |
| [`js/site-header.js`](js/site-header.js) | Shared header | All 3 prod HTML |
| [`js/animations.js`](js/animations.js) | Landing animations | [`index.html`](index.html) |

---

## 6. Infrastructure & configuration

### 6.1 docker-compose gaps

| Missing from [`docker-compose.yml`](docker-compose.yml) `backend.environment` | Default in [`config.py`](backend/app/config.py) | Confidence |
|-------------------------------------------------------------------------------|--------------------------------------------------|------------|
| `PIPELINE_TARGET_WORDS` | 60 | 🟢 High |
| `PIPELINE_INTERVAL_MINUTES` | varies | 🟢 High |
| `PIPELINE_AUTORUN` | varies | 🟡 Medium |
| `GROK_MODEL` | `grok-4` | 🟢 High |
| `DEFAULT_USER_ID` | 1 | 🟢 High |
| Volume for `TOPICS_DIR` (`/data/topics`) | — | 🟢 High |
| Volume for `backend/data/` (SQLite fallback) | — | 🟡 Medium |

### 6.2 .gitignore issue

[`.gitignore`](.gitignore) line 5: `.env.*` blocks **all** env example files.

| File | Should be tracked? | Currently | Confidence |
|------|-------------------|-----------|------------|
| `.env`, `backend/.env` | No | Ignored ✅ | 🟢 High |
| `backend/.env.example` | Yes (template) | Blocked by `.env.*` ❌ | 🟢 High |
| `backend/data/*.db` | No | Ignored ✅ | 🟢 High |

### 6.3 Repo hygiene (local artifacts)

| Path | In git? | Should be in git? | Confidence |
|------|---------|-------------------|------------|
| `backend/data/test.db-journal` | Untracked | No | 🟢 High |
| `backend/data/app.db` | Ignored | No | 🟢 High |

---

## 7. Documentation drift

| Document | Claim | Reality | Confidence |
|----------|-------|---------|------------|
| [`README.md`](README.md) L7 | `pytest (16)` | **36** tests collected | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md) §6 | `POST /topic`, `GET /topic/{id}/report` | `/api/pipeline/run`, `/overview`, `/queue`, `/runs` | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md) §9 | Paths like `db/models.py`, `services/mistral.py` | `backend/app/db/models.py`, `app/services/mistral_analyzer.py` | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md) v2 table | `pipeline_target_words` default 45 | [`config.py`](backend/app/config.py) default **60** | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md) §1 SQL | Illustrative schema | Actual: [`backend/app/db/models.py`](backend/app/db/models.py) | 🟢 High |
| [`editor-extract/README.md`](editor-extract/README.md) | `frontend/public/assets/wordlist/` | Path does not exist | 🟢 High |
| [`Deutsch Essay Design System/readme.md`](Deutsch%20Essay%20Design%20System/readme.md) | Points to root `images/`, `worte/` | Accurate for prod; DS also has own `assets/` | 🟢 High |

---

## 8. Repository size breakdown

| Path | Approx. size | In production runtime | Confidence |
|------|--------------|----------------------|------------|
| [`Deutsch Essay Design System/`](Deutsch%20Essay%20Design%20System/) | ~65 MB | No | 🟡 Medium (du measured in sandbox) |
| [`images/`](images/) | ~2.7 MB | Yes | 🟡 Medium |
| [`worte/`](worte/) | ~2.4 MB | Yes | 🟡 Medium |
| [`screenshots/`](screenshots/) | ~1.4 MB | Docs only | 🟡 Medium |
| [`backend/`](backend/) | ~684 KB | Yes | 🟡 Medium |
| [`editor-extract/`](editor-extract/) | ~296 KB | No | 🟡 Medium |

---

## 9. Backend module import graph (reference)

```
main.py
├── api/routes: essays, health, phrases, topics, words, pipeline
├── db: models, session, init_data
├── config.settings
└── startup: pipeline.scheduler, services.topic_pack_service

runner.py (orchestrator)
├── discovery, extraction, enrichment, supplement, normalize
├── mistral_http (via enrichment/extraction/supplement)
└── services.topic_pack_service

scheduler.py
├── runner.run_pipeline
└── topics_catalog.pick_new_topics

scripts-only (NOT in runner):
├── content_llm.py, verify.py          ← reprocess_topic.py
└── wiktionary_grammar.py, grammar_schema.py  ← backfill_grammar.py
```

Full pipeline modules: [`backend/app/pipeline/`](backend/app/pipeline/).

---

## 10. Prioritized remediation plan

### Phase 1 — Low risk cleanup

| # | Action | Confidence | Effort |
|---|--------|------------|--------|
| 1.1 | Delete orphans from §2.1 | 🟢 High | S |
| 1.2 | Fix [`.gitignore`](.gitignore) to allow `!.env.example`; add [`backend/.env.example`](backend/.env.example) | 🟢 High | S |
| 1.3 | Update [`README.md`](README.md) test count; refresh [`PIPELINE.md`](PIPELINE.md) API paths and defaults | 🟢 High | S |

### Phase 2 — Consolidation

| # | Action | Confidence | Effort |
|---|--------|------------|--------|
| 2.1 | Single canonical asset tree: `images/` + `worte/`; DS references or symlinks | 🟡 Medium | M |
| 2.2 | Single screenshot set for README | 🟡 Medium | S |
| 2.3 | Decide fate of [`editor-extract/`](editor-extract/): archive branch vs add `package.json` + build | 🟢 High | M–L |
| 2.4 | Extract [`pipeline.html`](pipeline.html) inline JS → [`js/pipeline.js`](js/pipeline.js) | 🟢 High | M |

### Phase 3 — Architectural (highest impact)

| # | Action | Confidence | Effort |
|---|--------|------------|--------|
| 3.1 | **Unify pipeline:** wire v3 into `runner.py` OR delete v3 modules + scripts | 🟢 High | L |
| 3.2 | Call `normalize_grammar_data()` on all word writes | 🟢 High | M |
| 3.3 | Add Alembic migrations; remove ad-hoc ALTER | 🟢 High | M |
| 3.4 | Normalize topic casing at all API entry points | 🟢 High | S |
| 3.5 | Shared `mistral_http` + shared Wiktionary client | 🟢 High | M |
| 3.6 | HTTP-mock tests for discovery, enrichment, extraction | 🟢 High | L |
| 3.7 | Pass `PIPELINE_*` env vars in [`docker-compose.yml`](docker-compose.yml) | 🟢 High | S |
| 3.8 | Migrate FastAPI to lifespan handlers | 🟢 High | S |

---

## 11. Items explicitly NOT recommended to delete without decision

| Path | Reason to keep | Confidence |
|------|----------------|------------|
| [`Deutsch Essay Design System/`](Deutsch%20Essay%20Design%20System/) entire folder | Active design reference if team uses DS gallery | 🔴 Low — business decision |
| [`editor-extract/`](editor-extract/) | Documented migration target | 🟡 Medium |
| [`backend/scripts/`](backend/scripts/) | Useful maintenance; just not wired to CI | 🟢 High |
| [`PIPELINE.md`](PIPELINE.md) | Valuable architecture doc — needs update, not deletion | 🟢 High |
| [`screenshots/`](screenshots/) except `Deutsch_2.png` | Used by README | 🟢 High |

---

## 12. Verification commands (for Claude or human re-audit)

```bash
# Test count
cd backend && pytest --collect-only -q

# Unused file grep examples
rg 'word-card\.html' .
rg 'botanical-top|decor-foot|wash-orange' .
rg 'Deutsch_2' .

# Dead symbols
rg 'normalize_grammar_data|enrich_word\(|_DDG_QUERIES' backend/

# Compose mounts
rg 'volumes:' -A20 docker-compose.yml

# Pipeline v3 imports from app (should be empty)
rg 'content_llm|verify|wiktionary_grammar|grammar_schema' backend/app/pipeline/runner.py
```

---

## 13. Changelog of this audit

| Field | Value |
|-------|-------|
| Files analyzed | ~280 paths (excl. `.git`, `node_modules`, `__pycache__`) |
| HTML files | 27 |
| Python files (backend) | 54 |
| Tests collected | 36 |
| Git changes made | None (report only) |
| Follow-up | User may request Phase 1 cleanup or ADR for pipeline v2 vs v3 |

---

## 14. Re-audit delta (2026-07-03, post-`schreiben` page)

### New production surface

| File | Role | In compose? | Confidence |
|------|------|-------------|------------|
| [`schreiben.html`](schreiben.html) | Essay roadmap / Pomodoro / Kli page | ✅ [`docker-compose.yml`](docker-compose.yml) L46 | 🟢 High |
| [`css/schreiben.css`](css/schreiben.css) | Styles for Schreiben | ✅ (via `css/` mount) | 🟢 High |
| [`js/schreiben.js`](js/schreiben.js) | Roadmap leaves, WASH brushes, Pomodoro | ✅ (via `js/` mount) | 🟢 High |

**Production HTML count:** 3 → **4** (`index`, `editor`, `schreiben`, `pipeline`).

### New images — usage check

| File | Referenced by | Status | Confidence |
|------|---------------|--------|------------|
| [`images/mountains-corner.png`](images/mountains-corner.png) | [`schreiben.html`](schreiben.html) L15 | ✅ Used | 🟢 High |
| [`images/timer-wash.png`](images/timer-wash.png) | [`css/schreiben.css`](css/schreiben.css) L106 | ✅ Used | 🟢 High |
| [`images/roadmap-leaf-1.png`](images/roadmap-leaf-1.png) | [`js/schreiben.js`](js/schreiben.js) L181 | ✅ Used | 🟢 High |
| [`images/roadmap-leaf-2.png`](images/roadmap-leaf-2.png) | [`js/schreiben.js`](js/schreiben.js) L182 | ✅ Used | 🟢 High |
| [`images/roadmap-leaf-3.png`](images/roadmap-leaf-3.png) | [`js/schreiben.js`](js/schreiben.js) L183 | ✅ Used | 🟢 High |
| [`images/roadmap-vine.png`](images/roadmap-vine.png) | **No references** (`rg roadmap-vine` → none) | ❌ **Unused — delete candidate** | 🟢 High |

### Navigation gap (not orphan, but inconsistent)

| Issue | Evidence | Confidence |
|-------|----------|------------|
| [`index.html`](index.html) and [`pipeline.html`](pipeline.html) link **Schreiben → `editor.html`** | `href="editor.html"` on nav | 🟢 High |
| [`schreiben.html`](schreiben.html) is not linked from other prod pages | No inbound `schreiben.html` links in HTML | 🟢 High |

**Note:** `schreiben.html` is deployed but reachable only by direct URL until nav is updated.

### Unchanged orphan list (still valid)

All items from §2.1 remain unused: [`word-card.html`](word-card.html), [`screenshots/Deutsch_2.png`](screenshots/Deutsch_2.png), DS orphans (`botanical-top`, `decor-foot`, `wash-orange`, DS `autumn.png`), [`deutsch-essay-editor.pptx`](Deutsch%20Essay%20Design%20System/deutsch-essay-editor.pptx).

### Do not commit

| Path | Reason |
|------|--------|
| `backend/data/test.db-journal` | Local SQLite artifact; gitignored |

---

*End of audit. For questions about a specific finding, search this file by filename or confidence level.*
