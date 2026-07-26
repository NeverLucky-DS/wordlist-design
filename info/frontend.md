# Frontend

Vanilla HTML/CSS/JS. No bundler. Cache bust via `?v=N` query params on each
`<link>`/`<script>` tag (bump the number when the file's content changes).

**Проверено против кода: 2026-07-26.** Раньше файл описывал `index.html` через
`js/app.js` + `js/animations.js` + `css/styles.css` — все три удалены сегодня
(`ls js/ css/` подтверждает отсутствие). Текущая реализация Wörterbuch —
`js/wb-page.js` + `js/wb-card.js` + `css/woerterbuch.css`, ни один из них не
упоминался. Backend-матрица тоже врала: `GET /api/words` не существует,
`index.html` ходит в `/api/vocab/*`.

## Pages

| File | Purpose | JS | CSS |
|------|---------|----|----|
| [`index.html`](../index.html) | Wörterbuch — search-and-spread lookup + personal word-list drawer | `site-header.js`, `words-data.js`, `wb-card.js`, `wb-page.js` | `site-header.css`, `woerterbuch.css` |
| [`schreiben.html`](../schreiben.html) | Essay roadmap — Pomodoro, stage drafts, drawer tools | `site-header.js`, `words-data.js`, `schreiben-api.js`, `analysis-waiting-phrases.js`, `schreiben.js` | `site-header.css`, `schreiben.css` |
| [`pipeline.html`](../pipeline.html) | Vocab-ingestion + enrichment ops dashboard | `site-header.js`, `pipeline.js`, `enrich.js` | `site-header.css`, `pipeline.css` |

Confirmed by grepping `<script src=` in the three HTML files directly — this
is the complete, exact list each page loads, nothing implied.

**Navigation:** all three pages use the same open editorial
`Essay / Pipeline / Wörterbuch` topbar. The markup is repeated in the static HTML
files; watercolor visuals, responsive behavior and active brush marks are shared
through `site-header.css`, `site-header.js` and `images/header/`.

## JS modules

### [`js/words-data.js`](../js/words-data.js) — shared brush map (55 lines)

The **single source** for level+POS → `worte/*.png` background. Loaded by both
`index.html` (for `wb-card.js`) and `schreiben.html` (for `schreiben.js`);
`pipeline.html` has no words on it and does not load this file.

| Symbol | Role |
|--------|------|
| `WASH` | 15 keys (`B1\|der` … `C1\|adj`) → brush filename |
| `typeKey(w)` | Maps a local `{pos, art}` object to a WASH type key |
| `brushOf(w)` | For local objects (`schreiben.js`'s demo `WORDS`) |
| `brushOfCard(card)` | For `/api/vocab/*` cards, which arrive with `band`/`type` already resolved server-side (`app/vocab/norm.py`) |

`PIPELINE_WASHES` and the byte-identical copy of `WASH` that used to live in
`wb-card.js` are both gone — deduplicated in this branch.

### [`js/wb-card.js`](../js/wb-card.js) — Wörterbuch card renderer (493 lines)

Builds one word card (`wortkarte()`) from a `card_out` object: head, meanings,
example, usage/collocations, and a POS-conditional grammar tab
(`grammarModel()` returns `null` for adverbs/incomparable adjectives, so the
tab doesn't render where there is nothing to say).

### [`js/wb-page.js`](../js/wb-page.js) — Wörterbuch page shell (525 lines)

Drives the "spread" layout: search results on the left, the opened card takes
the opposite column, personal list in a right-edge drawer. Talks to
`/api/vocab/search`, `/api/vocab/entry/{lemma}`, `/api/vocab/list`
(GET/POST/DELETE), `/api/vocab/list/stats`. Reads `window.WB_API`/`WB_DEMO`
hooks that are now dead in every supported setup (nothing sets them — the
`:8799` file-server prototype that used `WB_DEMO` was deleted 2026-07-25); left
in place rather than unpicked from ~8 call sites.

### [`js/schreiben.js`](../js/schreiben.js) — Schreiben (2377 lines)

| Symbol | Role |
|--------|------|
| `STAGES` | 4 essay stages — `einleitung`, `arg1`, `arg2`, `schluss` — each with a Klischee (`kli`) pool; drives the roadmap nodes 1:1 (`buildRoadmap()` does `STAGES.forEach`) |
| `store` / `localStorage` | Offline dirty copy; server hydrates canonical owner-scoped essay list |
| `persistEssayToApi()` | Debounced autosave with explicit dirty/saving/saved/offline states |
| `loadAnalysisHistory()` | Immutable full/part timeline and stale-result handling |
| `pollAnalysis()` | Resumable background run status, cancellation and result hydration |
| `THEMEN` | Static theme picker (12 topics) |
| `WORDS` | Static demo word list (12 words, all tagged `Technologie`) — the in-editor "Wörterbuch" tool renders from this, not from `/api/vocab/*` |
| `KLI_PARTS`, `loadKlischees()`, `kliFiltered()` | Fetch and paginate `/api/phrases/templates` |
| `buildRoadmap()` | SVG path + decorative leaves |
| `openTool()` | Inline expanding tool cards (Wörterbuch / Hilfen) |

⚠️ `schreiben.js` makes **zero** calls to `/api/vocab/*` (grepped: 0 matches) —
the personal word list built in `index.html` and the words shown while writing
an essay are two disconnected data sets. See `info/PLANS.md` A0.

### [`js/schreiben-api.js`](../js/schreiben-api.js) — API bridge

Exports `window.SchreibenApi`: essay CRUD, versions, background analysis
start/status/history/cancel, health probe and the legacy stream bridge. Calls
every route under `/api/essays/*` documented in `info/backend-api.md`.

### [`js/analysis-waiting-phrases.js`](../js/analysis-waiting-phrases.js)

Approved German culture/history fact pool (`ANALYSIS_WAITING_PHRASES`, 61
entries). While the real step indicator
tracks server progress, Schreiben rotates one entertainment line every 10
seconds and excludes the five most recently shown indices.

### [`js/site-header.js`](../js/site-header.js)

Shared theme toggle plus the account dialog (register/login/logout/delete),
exposes `window.SiteAuth` (`refresh`, `open`, `getState`) and dispatches
`site-auth-change`, used by Schreiben and the Wörterbuch drawer to rehydrate
after identity changes. Calls `/api/auth/me`, `/api/auth/register`,
`/api/auth/login`, `/api/auth/logout`, `/api/auth/account`.

### [`js/pipeline.js`](../js/pipeline.js) — ingestion dashboard (168 lines)

Talks to `/api/vocab/{build,status,stats,words,word}` — the **raw
pre-enrichment** dictionary build (`vocab.db`), not the enriched cards. Launch
a build, watch every stage, browse the saved words per source.

### [`js/enrich.js`](../js/enrich.js) — enrichment control panel (382 lines)

Saves this account's Mistral key (`PUT`/`DELETE /api/auth/mistral-key`),
starts/stops its worker and polls progress
(`/api/vocab/enrich/{start,stop,status,progress,cards,card,requeue}`), plus the
admin fleet table (`/api/vocab/enrich/fleet`, `fleet/start`, `fleet/stop`). The
Mistral key itself never lives in the browser past the one `PUT` call.

## CSS

| File | Used by |
|------|---------|
| `css/woerterbuch.css` | `index.html` — spread layout, card, drawer, dark theme |
| `css/schreiben.css` | `schreiben.html` — roadmap, drawer, Pomodoro |
| `css/pipeline.css` | `pipeline.html` — dashboard tables |
| `css/site-header.css` | All production pages — illustrated topbar, active brush mask and responsive navigation |

`css/styles.css` (the old `index.html` stylesheet) and `js/app.js` /
`js/animations.js` (the old `index.html` scripts, plus landing-page
scroll/entrance animation) are gone — deleted in this branch as dead code with
zero remaining `<script>`/`<link>` references.

Design tokens: CSS variables in each file (`--ink`, `--rose`, level colors). Brush images from [`worte/`](../worte/). Decor from [`images/`](../images/).

## Assets

| Folder | Count | Usage |
|--------|-------|-------|
| [`worte/`](../worte/) | 15 PNG | Level×POS watercolor brushes (`B1_Adjectives_...`, etc.), keyed by `WASH` in `words-data.js` |
| [`images/`](../images/) | 19 PNG (15 at root + 4 in `header/`) | Decor, schreiben bg, tool icons, roadmap leaves, shared header artwork |

Exhaustive per-file mapping (which CSS/JS references which PNG, alpha-channel
classification for compression) lives in `info/CRITICAL-LINKS.md` §3–4 — not
duplicated here to avoid the two copies drifting.

## Frontend ↔ Backend matrix

| Page | Endpoints used |
|------|----------------|
| `index.html` | `/api/vocab/search`, `/api/vocab/entry/{lemma}`, `/api/vocab/list` (GET/POST), `/api/vocab/list/stats`, `/api/vocab/list/{lemma}` (DELETE) — via `wb-page.js` |
| all pages | `/api/auth/me`, `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/account` — via `site-header.js` |
| `schreiben.html` | `/api/essays` + `/versions` + `/analyses` background lifecycle (`schreiben-api.js`); `GET /api/phrases/templates` (`schreiben.js`) |
| `pipeline.html` | `/api/vocab/{build,status,stats,words,word}` (`pipeline.js`, build is admin-only); `/api/vocab/enrich/*` + `PUT`/`DELETE /api/auth/mistral-key` (`enrich.js`, most of `enrich/*` require login, `fleet/*` require admin) |

`GET /api/words` from the old version of this file **does not exist** — the
`words` router was removed along with `/api/topics/*` and the list-all
`GET /api/phrases`; see `info/backend-api.md`.
