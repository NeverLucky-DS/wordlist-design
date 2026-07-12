# Frontend

Vanilla HTML/CSS/JS. No bundler. Cache bust via `?v=N` query params.

## Pages

| File | Purpose | JS | CSS |
|------|---------|----|----|
| [`index.html`](../index.html) | Wörterbuch — word grid, filters, detail card | `site-header.js`, `app.js`, `animations.js` | `site-header.css`, `styles.css` |
| [`schreiben.html`](../schreiben.html) | Essay roadmap — Pomodoro, stage drafts, drawer tools | `site-header.js`, `schreiben-api.js`, `schreiben.js` | `site-header.css`, `schreiben.css` |
| [`pipeline.html`](../pipeline.html) | Pipeline ops dashboard | `site-header.js`, `pipeline.js` | `site-header.css`, `pipeline.css` |

**Navigation:** all three pages use the same open editorial
`Essay / Pipeline / Wörterbuch` topbar. The markup is repeated in the static HTML
files; watercolor visuals, responsive behavior and active brush marks are shared
through `site-header.css`, `site-header.js` and `images/header/`.

## JS modules

### [`js/app.js`](../js/app.js) — Wörterbuch (~834 lines)

| Symbol | Role |
|--------|------|
| `WASH` / `brushOf()` | Maps word level+POS → `worte/*.png` background |
| `WORDS` | Static seed words (fallback) |
| `filtered()`, `renderList()` | Search, category, level filters |
| `renderDetail()`, `openDetail()` | Word detail panel + grammar blocks |
| `loadApiWords()` | `GET /api/words` → merges into list |

### [`js/schreiben.js`](../js/schreiben.js) — Schreiben (~1052 lines)

| Symbol | Role |
|--------|------|
| `STAGES` | 6 essay stages (Einleitung → Schluss) |
| `store` / `localStorage` | Local essay lifecycle; editable essays sync to the backend when available |
| `THEMEN` | Static theme picker (12 topics); comment: pipeline DB later |
| `buildRoadmap()` | SVG path + decorative leaves |
| `openTool()` | Inline expanding tool cards (Wörterbuch / Hilfen) |
| `WORDS` / `WASH` | Static word data (duplicated from `app.js`) |

### [`js/schreiben-api.js`](../js/schreiben-api.js) — API bridge

Exports `window.SchreibenApi`: essay create/update, health probe and streamed analysis.

### [`js/site-header.js`](../js/site-header.js)

Shared theme-toggle behavior. Primary navigation uses direct links and needs no
dropdown JavaScript.

### [`js/animations.js`](../js/animations.js)

Landing page scroll/entrance animations (`index.html` only).

## CSS

| File | Used by |
|------|---------|
| `css/styles.css` | `index.html` — word grid, detail, watercolor column |
| `css/schreiben.css` | `schreiben.html` — roadmap, drawer, Pomodoro |
| `css/pipeline.css` | `pipeline.html` — dashboard tables |
| `css/site-header.css` | All production pages — illustrated topbar, active brush mask and responsive navigation |

Design tokens: CSS variables in each file (`--ink`, `--rose`, level colors). Brush images from [`worte/`](../worte/). Decor from [`images/`](../images/).

## Assets

| Folder | Count | Usage |
|--------|-------|-------|
| [`worte/`](../worte/) | 15 PNG | Level×POS watercolor brushes (`B1_Adjectives_...`, etc.) |
| [`images/`](../images/) | 20 PNG | Decor, schreiben bg, tool icons, roadmap leaves and 4 shared header artworks |

## Frontend ↔ Backend matrix

| Page | Endpoints used |
|------|----------------|
| `index.html` | `GET /api/words` (optional overlay) |
| `schreiben.html` | `/api/essays`, `/api/essays/{id}/analyze/stream` |
| `pipeline.html` | `GET /api/pipeline/overview`, `POST /api/pipeline/queue`, `POST /api/pipeline/run` |
