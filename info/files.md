# Canonical file tree

Only files that matter for development/review.

```
wordlist design/
├── info/                    ← YOU ARE HERE (project docs)
├── index.html               # Wörterbuch
├── editor.html              # Essay editor + AI analysis
├── schreiben.html           # Essay roadmap (Pomodoro, stages)
├── pipeline.html            # Pipeline dashboard
├── docker-compose.yml
├── nginx.conf
├── Dockerfile
├── README.md                # User-facing intro + screenshots
├── PIPELINE.md              # Long pipeline design doc (partially stale)
│
├── css/
│   ├── styles.css           # Wörterbuch
│   ├── editor.css           # Editor
│   ├── schreiben.css        # Schreiben page
│   ├── pipeline.css         # Pipeline dashboard
│   └── site-header.css      # Shared nav
│
├── js/
│   ├── app.js               # Wörterbuch logic
│   ├── editor.js            # Editor logic
│   ├── schreiben.js         # Roadmap logic
│   ├── editor-api.js        # Fetch wrapper for editor
│   ├── site-header.js       # Nav dropdown
│   └── animations.js        # index.html animations
│
├── images/                  # Decor PNGs (14 files)
├── worte/                   # Brush PNGs by level×POS (15 files)
├── screenshots/             # README demo images (8 files)
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

## Removed (2026-07-03 cleanup)

| Removed | Reason |
|---------|--------|
| `Deutsch Essay Design System/` (~65 MB) | Duplicate of prod assets + React prototypes; not deployed |
| `editor-extract/` | Incomplete React migration stub; no package.json |
| `word-card.html` | Orphan mock |
| `screenshots/Deutsch_2.png` | Unreferenced |
| `images/roadmap-vine.png` | Unreferenced |

## Gitignored (local only)

- `.env`, `backend/.env`
- `backend/data/*.db`
- `__pycache__/`, `.venv/`
