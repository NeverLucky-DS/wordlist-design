# Frontend

Vanilla HTML/CSS/JS. No bundler. Cache bust via `?v=N` query params.

## Pages

| File | Purpose | JS | CSS |
|------|---------|----|----|
| [`index.html`](../index.html) | Wörterbuch — word grid, filters, detail card | `site-header.js`, `app.js`, `animations.js` | `site-header.css`, `styles.css` |
| [`editor.html`](../editor.html) | Essay editor — 4 sections, Kli, analysis, word panel | `site-header.js`, `editor-api.js`, `editor.js` | `site-header.css`, `editor.css` |
| [`schreiben.html`](../schreiben.html) | Essay roadmap — Pomodoro, stage drafts, drawer tools | `schreiben.js` | `schreiben.css` |
| [`pipeline.html`](../pipeline.html) | Pipeline ops dashboard | `site-header.js` + **inline script** | `site-header.css`, `pipeline.css` |

**Nav note:** `index.html` / `pipeline.html` link Schreiben → `editor.html`. `schreiben.html` is deployed but not linked from other pages yet.

## JS modules

### [`js/app.js`](../js/app.js) — Wörterbuch (~834 lines)

| Symbol | Role |
|--------|------|
| `WASH` / `brushOf()` | Maps word level+POS → `worte/*.png` background |
| `WORDS` | Static seed words (fallback) |
| `filtered()`, `renderList()` | Search, category, level filters |
| `renderDetail()`, `openDetail()` | Word detail panel + grammar blocks |
| `loadApiWords()` | `GET /api/words` → merges into list |

### [`js/editor.js`](../js/editor.js) — Editor (~1593 lines)

| Area | Key functions |
|------|---------------|
| State | `state` object — sections, essay id, errors, words |
| Persistence | `persistEssayNow()`, `schedulePersistEssay()` → PATCH `/api/essays/{id}` |
| Analysis | `initAnalyze()` → `EditorApi.streamAnalyze()` SSE |
| Annotations | `mapErrorsToSections()`, `renderAnnotationPopover()`, `onAnnotationAction()` |
| Sections | `renderMap()`, `selectSection()`, `renderEditorText()` |
| Kli (clichés) | `renderKlischees()`, `insertCliche()` — loads `GET /api/phrases` |
| Word panel | `renderWordList()`, `openCard()` — loads `GET /api/words` |
| Pomodoro | `initPomo()`, `togglePomo()` |
| Boot | `initBackendBridge()` → topics/words/phrases from API; `boot()` |

### [`js/schreiben.js`](../js/schreiben.js) — Schreiben (~1052 lines)

| Symbol | Role |
|--------|------|
| `STAGES` | 6 essay stages (Einleitung → Schluss) |
| `store` / `localStorage` | Essay lifecycle (drafts, snapshots, reports) — **backend hookup planned** |
| `THEMEN` | Static theme picker (12 topics); comment: pipeline DB later |
| `buildRoadmap()` | SVG path + decorative leaves |
| `openTool()` | Inline expanding tool cards (Wörterbuch / Hilfen) |
| `WORDS` / `WASH` | Static word data (duplicated from `app.js`) |

**No API calls yet** — unlike `editor.js`.

### [`js/editor-api.js`](../js/editor-api.js) — API bridge

IIFE exporting `window.EditorApi`: `createEssay`, `updateEssay`, `listWords`, `listPhrases`, `queueWord`, `streamAnalyze`, `probeHealth`.

### [`js/site-header.js`](../js/site-header.js)

Shared nav dropdown behavior.

### [`js/animations.js`](../js/animations.js)

Landing page scroll/entrance animations (`index.html` only).

## CSS

| File | Used by |
|------|---------|
| `css/styles.css` | `index.html` — word grid, detail, watercolor column |
| `css/editor.css` | `editor.html` — manuscript, annotations, Kli |
| `css/schreiben.css` | `schreiben.html` — roadmap, drawer, pomodoro |
| `css/pipeline.css` | `pipeline.html` — dashboard tables |
| `css/site-header.css` | All pages — topbar |

Design tokens: CSS variables in each file (`--ink`, `--rose`, level colors). Brush images from [`worte/`](../worte/). Decor from [`images/`](../images/).

## Assets

| Folder | Count | Usage |
|--------|-------|-------|
| [`worte/`](../worte/) | 15 PNG | Level×POS watercolor brushes (`B1_Adjectives_...`, etc.) |
| [`images/`](../images/) | 16 PNG | Decor, schreiben bg, tool icons, roadmap leaves |

## Frontend ↔ Backend matrix

| Page | Endpoints used |
|------|----------------|
| `index.html` | `GET /api/words` (optional overlay) |
| `editor.html` | `/api/essays`, `/api/words`, `/api/phrases`, `/api/essays/{id}/analyze/stream` |
| `schreiben.html` | — (static) |
| `pipeline.html` | `GET /api/pipeline/overview`, `POST /api/pipeline/queue`, `POST /api/pipeline/run` |
