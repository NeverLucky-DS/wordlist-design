# Project map (read this first)

Compact reference for AI/human review. **Start here** instead of scanning the whole repo.

| Doc | Contents |
|-----|----------|
| [CRITICAL-LINKS.md](CRITICAL-LINKS.md) | **Safe-delete map — read before refactoring** |
| [PLANS.md](PLANS.md) | **Work queue + open problems — pick the top item when idle** |
| [architecture.md](architecture.md) | Deploy, nginx, services, data flow |
| [frontend.md](frontend.md) | HTML pages, JS/CSS modules, assets |
| [backend-api.md](backend-api.md) | REST endpoints |
| [AUDIT-2026-07-26.md](AUDIT-2026-07-26.md) | **Приоритеты 1-й и 2-й очереди, с замером на пункт** |
| [tooling.md](tooling.md) | **Инструменты качества: линтер, типы, снапшоты, фаззинг, хуки** |
| [data-model.md](data-model.md) | PostgreSQL tables |
| [files.md](files.md) | Canonical file tree (what matters) |
| [graph.md](graph.md) | Code graph (Graphify) — how to navigate the repo structurally |

⚠️ **Устарели, доверять с проверкой (2026-07-26).** Все четыре описывают topic-pipeline,
которого больше нет: роутера `/api/pipeline/*` не существует, пакета
`backend/app/pipeline/` тоже, Grok не упоминается в `backend/` ни разу.

| Doc | Что в нём протухло |
|-----|--------------------|
| [pipeline.md](pipeline.md) | описывает удалённый v2-путь целиком |
| [backend-api.md](backend-api.md) | 7 несуществующих ручек `/api/pipeline/*` |
| [frontend.md](frontend.md) | `pipeline.html` как потребитель `/api/pipeline/*` |
| [architecture.md](architecture.md) | `GROK_API_KEY` в обязательных env, пакет `pipeline/` |
| [known-debt.md](known-debt.md) | переписан 2026-07-26; актуальный долг — в AUDIT |
| [AUDIT.md](AUDIT.md) | аудит от 2026-07-11, заменён AUDIT-2026-07-26 |

## One-paragraph summary

**Deutsch Essay Trainer** — B1–C1 German essay app. Vanilla HTML/JS frontend (nginx :8753) talks to FastAPI backend (:8000) + PostgreSQL. Users look words up in a 92 000-card dictionary (`index.html`), plan/write essays (`schreiben.html`), and ops drive the enrichment workers (`pipeline.html`). Backend uses Mistral for word enrichment and essay analysis; the dictionary itself is built offline from dictionary dumps + Wiktionary, with no LLM in that path.

## Production entry points

| URL | File | Backend |
|-----|------|---------|
| `/` | `index.html` | `/api/vocab/*` (search, entry, list). `GET /api/words` жив, но не зовётся ниоткуда |
| `/schreiben.html` | `schreiben.html` | `/api/auth/*`, `/api/essays/*` (localStorage offline copy) |
| `/pipeline.html` | `pipeline.html` | `/api/vocab/*` (`/api/pipeline/*` удалён вместе с topic-pipeline) |
| `/api/*` | — | all routes |
| `/health` | — | liveness |

## Do not waste tokens on

- `backend/scripts/`, `backend/audit_db.py` — manual maintenance CLIs
- `backend/data/` — local SQLite (gitignored)
- `graphify-out/` — generated code-graph artifact (gitignored); see [graph.md](graph.md) for how to use it
