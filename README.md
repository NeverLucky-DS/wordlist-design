# wordlist-design — Deutsch Essay Wörterbuch

Full-stack прототип тренажёра немецкого: словарь, редактор эссе, FastAPI backend, полуавтоматический пайплайн пополнения базы слов.

---

## Зачем этот проект (backend / AI)

Пет-проект уровня production-prototype: REST API, PostgreSQL, LLM-интеграция, тесты. Покрывает стек стажировки в разработке агентских backend-решений.

| Навык | Реализация |
|-------|------------|
| Python | backend, pipeline, скрипты |
| FastAPI | REST API, OpenAPI, async routes |
| PostgreSQL | слова, грамматика, прогресс |
| Тесты | pytest (`backend/tests/`) |
| LLM / агенты | пайплайн обогащения слов (Mistral), structured output |
| Async | async SQLAlchemy / httpx |
| Git, Docker | docker-compose, changelog |

---

## Стек

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend:** HTML/CSS/JS (прототип UI), editor-extract (React + FastAPI)
- **AI:** Mistral API — обогащение карточек слов
- **Тесты:** pytest
- **Инфра:** Docker Compose, uv

---

## Страницы

- `index.html` — словарь (Wörterbuch)
- `editor.html` — редактор эссе
- `word-card.html` — карточка слова
- `backend/` — API и пайплайн
- `PIPELINE.md` — спецификация пайплайна пополнения слов

---

## Быстрый старт

```bash
cp .env.example .env
# MISTRAL_API_KEY и DATABASE_URL
docker compose up --build
```

API: `http://127.0.0.1:8000/docs`  
Тесты: `uv run pytest`

---

## Архитектура (кратко)

```
UI (HTML / editor) → FastAPI routes → services / pipeline → PostgreSQL
                              ↓
                         Mistral API
```

---

## Скриншоты

Картинки клади в `docs/screenshots/` и вставляй в README:

```markdown
![Словарь](docs/screenshots/woerterbuch.png)
```

| Файл | Что снять |
|------|-----------|
| `woerterbuch.png` | главная страница словаря |
| `word-card.png` | карточка слова с грамматикой |
| `editor.png` | редактор эссе |
| `api-docs.png` | Swagger `/docs` |
| `pipeline.png` | UI или лог пайплайна пополнения слов |

GitHub показывает изображения из репозитория автоматически после commit.
