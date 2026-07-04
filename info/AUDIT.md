# Technical Debt & Files Audit

> **Date:** 2026-07-04  
> **Branch:** `main` (post-Schreiben essay lifecycle)  
> **Method:** static grep, import graph, asset cross-ref, pytest collection  
> **Prior audit:** [`known-debt.md`](known-debt.md) (rolling short list)

### Confidence scale

| Level | Meaning |
|-------|---------|
| 🟢 **High** | Verified by grep / file listing / direct read |
| 🟡 **Medium** | Strong inference, not runtime-tested |
| 🔴 **Low** | Judgment call |

---

## Executive summary

| Area | Status | vs 2026-07-03 |
|------|--------|---------------|
| Orphan files | 🟢 Good | −2 PNG removed (`mountains-corner`, `drawer-head-wash`); DS/editor-extract gone |
| Asset duplication | 🟢 Good | Single `images/` + `worte/` |
| Frontend code duplication | 🟡 | `WORDS`/`WASH` still ×3; `schreiben.js` grew to **1052** lines |
| Backend pipeline | 🔴 Unchanged | v2 prod vs v3 scripts split |
| Schema/migrations | 🔴 Unchanged | No Alembic |
| Documentation | 🟢 | `info/` maintained; this audit |

**Biggest new frontend debt:** `schreiben.js` essay lifecycle (localStorage) parallel to `editor.js` (backend API) — two writing flows without integration.

---

## 1. Unused files (current)

### Removed this audit 🟢 High

| File | Size | Reason |
|------|------|--------|
| `images/mountains-corner.png` | 680 KB | Replaced by `background_schreiben.png`; zero references |
| `images/drawer-head-wash.png` | 242 KB | Never referenced in CSS/HTML/JS |

### All production assets — used ✅

| Folder | Files | Confidence |
|--------|-------|------------|
| `images/` | 16 PNG (after cleanup) | 🟢 High |
| `worte/` | 15 brush PNG | 🟢 High |
| `screenshots/` | 8 PNG | README only 🟡 Medium |

### Intentionally not production

| Path | Role | Confidence |
|------|------|------------|
| `info/` | Dev docs (~40 KB) | 🟢 High |
| `backend/scripts/`, `audit_db.py` | Manual maintenance | 🟢 High |
| `PIPELINE.md` | Long design doc (partially stale) | 🟢 High |
| `backend/data/` | Local SQLite (gitignored) | 🟢 High |

---

## 2. Image inventory (`images/`)

| File | ~Size | Used by | Status |
|------|-------|---------|--------|
| `background_schreiben.png` | 894 KB | `schreiben.css` body bg | ✅ |
| `autumn.png` | 861 KB | `editor.js` | ✅ (large — compress candidate) |
| `kli-1/2/3.png` | 350–418 KB | `editor.css`, `schreiben.css` | ✅ |
| `abstract-watercolor-column.png` | 288 KB | `styles.css`, `editor.css`, `pipeline.css`, `schreiben.css` | ✅ |
| `Deklination.png` | 221 KB | `styles.css`, `schreiben.css` | ✅ |
| `Verwendung.png` | 201 KB | `styles.css`, `editor.css` | ✅ |
| `tool-card-wash.png` | 178 KB | `schreiben.css` | ✅ |
| `timer-wash.png` | 157 KB | `schreiben.css` | ✅ |
| `tool-woerterbuch.png` | 56 KB | `schreiben.html` | ✅ |
| `roadmap-leaf-1/2/3.png` | 20–45 KB | `schreiben.js` | ✅ |
| `tool-hilfen.png` | 19 KB | `schreiben.html` | ✅ |
| `decor-head.png` | 5.5 KB | `styles.css`, `editor.css`, `schreiben.css` | ✅ |

**Optimization opportunity 🟡:** `background_schreiben.png` + `autumn.png` = ~1.7 MB — WebP or stronger PNG compression.

---

## 3. Frontend technical debt

| # | Issue | Severity | Confidence | Location |
|---|-------|----------|------------|----------|
| 1 | **Dual essay flows:** `editor.js` → backend API; `schreiben.js` → localStorage, no API | 🔴 High | 🟢 100% | `js/schreiben.js` L187–188 |
| 2 | **`WORDS` + `WASH` triplicated** | 🟡 Medium | 🟢 100% | `app.js`, `editor.js`, `schreiben.js` |
| 3 | **`schreiben.js` monolith** — 1052 lines (was 601) | 🟡 Medium | 🟢 100% | essay store, roadmap, tools, grammar |
| 4 | **`editor.js` monolith** — 1593 lines | 🟡 Medium | 🟢 100% | |
| 5 | **`pipeline.html` inline JS** ~350 lines | 🟡 Medium | 🟢 90% | no `js/pipeline.js` |
| 6 | **Two Schreiben pages** — `schreiben.html` (roadmap) vs `editor.html` (manuscript+AI); no cross-link | 🟡 Medium | 🟢 95% | |
| 7 | Nav stubs `href="#"` (Dashboard, Verlauf…) | 🟢 Low | 🟢 100% | all HTML |
| 8 | `THEMEN` in schreiben is static; comment says pipeline DB later | 🟡 Medium | 🟢 100% | `schreiben.js` L190–191 |

### Resolved since last audit ✅

- Nav Schreiben → `schreiben.html` on `index.html`, `pipeline.html` 🟢
- Tool PNGs wired in schreiben 🟢
- `background_schreiben.png` wired 🟢

---

## 4. Backend technical debt (unchanged)

| # | Issue | Severity | Confidence |
|---|-------|----------|------------|
| 1 | Pipeline **v2** (`runner`→`enrichment`) vs **v3** (`content_llm`, `verify` — scripts only) | 🔴 Critical | 🟢 95% |
| 2 | `normalize_grammar_data()` never called on word writes | 🔴 High | 🟢 95% |
| 3 | Alembic in `requirements.txt`, no `alembic/` dir | 🔴 High | 🟢 100% |
| 4 | Topic casing: API preserves case, runner lowercases | 🟡 Medium | 🟢 90% |
| 5 | 3× Wiktionary + 2× Mistral HTTP stacks | 🟡 Medium | 🟢 90% |
| 6 | `mistralai` package unused (no imports) | 🟡 Medium | 🟢 100% |
| 7 | `PIPELINE_*` env not in docker-compose | 🟡 Medium | 🟢 100% |
| 8 | `data/topics/*.yaml` missing — `/api/topics` empty in Docker | 🟡 Medium | 🟢 90% |
| 9 | Dead code: `_DDG_QUERIES`, `enrich_word()` | 🟢 Low | 🟢 95% |
| 10 | `datetime.utcnow()`, `@app.on_event` deprecated | 🟢 Low | 🟢 90% |
| 11 | `/health` no DB check | 🟢 Low | 🟢 100% |
| 12 | v1 startup cleanup every boot | 🟡 Medium | 🟢 90% |

**Tests:** 36 collected; discovery/enrichment/extraction not directly tested 🟢 High.

---

## 5. Infrastructure

| Change | Assessment | Confidence |
|--------|------------|------------|
| `docker-compose.yml` mounts `.:/usr/share/nginx/html` | Fixes stale inode on file replace; **exposes whole repo** via nginx (backend/, info/, .git) — OK for local dev only | 🟢 High |
| `PIPELINE_*` still absent from compose env | Can't tune pipeline without rebuild | 🟢 High |
| No `backend/.env.example` | `.gitignore` blocks `.env.*` | 🟢 High |

---

## 6. Documentation drift

| File | Issue | Confidence |
|------|-------|------------|
| `info/frontend.md` | Was stale on unwired assets — fixed in this audit | 🟢 |
| `info/known-debt.md` | Updated in this audit | 🟢 |
| `info/architecture.md` | Docker mount model needs update | 🟢 |
| `PIPELINE.md` | Still references target_words=45, old paths | 🟢 High |
| `info/files.md` | Listed removed orphans — fixed | 🟢 |

---

## 7. Priority roadmap

### Quick wins (low risk)

1. ~~Delete `mountains-corner.png`, `drawer-head-wash.png`~~ ✅ done
2. Extract shared `js/words-data.js` for WORDS/WASH
3. Remove unused `mistralai` from requirements
4. Add `!.env.example` to `.gitignore`

### Medium impact

5. Wire `schreiben.js` to `/api/essays` + `/api/words` (replace localStorage prototype)
6. Link `schreiben.html` ↔ `editor.html` or merge flows
7. Extract `js/pipeline.js`
8. Pass `PIPELINE_*` through docker-compose
9. Compress `background_schreiben.png`, `autumn.png`

### Architectural

10. Unify pipeline v2/v3
11. Alembic migrations
12. `normalize_grammar_data()` on all writes

---

## 8. Repo metrics

| Metric | Value |
|--------|-------|
| Source files (py/js/html/css/md) | ~79 |
| `js/schreiben.js` | 1052 lines |
| `js/editor.js` | 1593 lines |
| `images/` | 16 PNG (~5 MB) |
| `worte/` | 15 PNG (~2.4 MB) |
| `info/` | 8 docs (~40 KB) |
| pytest tests | 36 |
| Production HTML pages | 4 |

---

*Next audit: after schreiben↔backend integration or pipeline unification.*
