# Canonical file tree

Only files that matter for development/review.

```
wordlist design/
├── info/                    ← project docs (+ CRITICAL-LINKS.md)
├── index.html               # Wörterbuch
├── schreiben.html           # Essay roadmap (Pomodoro, stages)
├── pipeline.html            # Pipeline dashboard
├── docker-compose.yml
├── nginx.conf
├── Dockerfile
├── README.md
├── PIPELINE.md              # Long pipeline design doc (partially stale)
│
├── css/
│   ├── styles.css           # Wörterbuch
│   ├── schreiben.css        # Schreiben page
│   ├── pipeline.css         # Pipeline dashboard
│   └── site-header.css      # Shared nav (index, pipeline)
│
├── js/
│   ├── words-data.js        # Shared WASH + brushOf + PIPELINE_WASHES
│   ├── app.js               # Wörterbuch logic
│   ├── schreiben.js         # Roadmap logic
│   ├── pipeline.js          # Pipeline dashboard logic
│   ├── site-header.js       # Nav dropdown + theme toggle
│   └── animations.js        # index.html animations
│
├── images/                  # Decor PNGs (15 files)
├── worte/                   # Brush PNGs by level×POS (15 files)
│
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── schemas.py
    │   ├── api/routes/      # essays, words, phrases, topics, pipeline, health
    │   ├── services/        # repos + mistral_analyzer + wiktionary
    │   ├── db/              # models, session, init_data
    │   └── pipeline/        # runner, scheduler, discovery, enrichment, …
    ├── tests/               # pytest (36 tests)
    ├── scripts/             # manual maintenance only
    ├── audit_db.py          # manual DB audit CLI
    └── requirements.txt
```

## Removed (historical)

| Removed | Reason |
|---------|--------|
| `editor.html`, `editor.js`, `editor-api.js`, `editor.css` | Legacy parallel essay flow; not in nav |
| `images/autumn.png` | Editor-only asset |
| `screenshots/` | README demo images; not in UI |
| `Deutsch Essay Design System/` | Duplicate assets; not deployed |
| `editor-extract/` | Incomplete React stub |
| `word-card.html`, `screenshots/Deutsch_2.png` | Orphans |
| `images/roadmap-vine.png`, `mountains-corner.png`, `drawer-head-wash.png` | Unreferenced |

## Gitignored (local only)

- `.env`, `backend/.env`
- `backend/data/*.db`
- `__pycache__/`, `.venv/`
