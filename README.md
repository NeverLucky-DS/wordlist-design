# Deutsch Essay Trainer

**NLP / LLM** прототип для немецкого B1–C1: тематический словарь, essay roadmap (Schreiben), pipeline обогащения слов по теме.

**Репо:** https://github.com/NeverLucky-DS/wordlist-design

**Стек:** Mistral · Grok discovery · PostgreSQL · FastAPI · Docker · pytest (36)

## Страницы

| Страница | URL | Назначение |
|----------|-----|------------|
| Wörterbuch | http://localhost:8753 | Тематический словарь + API overlay |
| Schreiben | http://localhost:8753/schreiben.html | Essay roadmap, Pomodoro, инструменты |
| Pipeline | http://localhost:8753/pipeline.html | Очередь тем, автопилот, сбор слов |
| API docs | http://localhost:8000/docs | OpenAPI |

---

## Быстрый старт

Весь жизненный цикл — через `make` (запусти `make` без аргументов, чтобы увидеть все команды):

```bash
make setup     # uv sync + создаст backend/.env из шаблона
#              → впиши MISTRAL_API_KEY и GROK_API_KEY в backend/.env
make up        # соберёт и поднимет db + api + web, применит миграции,
#                дождётся готовности и напечатает все ссылки на localhost
```

| Команда | Что делает |
|---------|------------|
| `make up` / `make down` | поднять / остановить весь стек |
| `make logs` | логи всех сервисов |
| `make test` | тесты backend |
| `make migrate` | применить миграции БД |
| `make migration name="..."` | новая миграция из изменений моделей |
| `make db` | psql-шелл в контейнере БД |
| `make clean` | остановить и **удалить данные** (том БД) |

Ключи можно не задавать — стек поднимется, но enrichment/анализ без них работать не будут.

---

## Архитектура

```
index.html / schreiben.html / pipeline.html
              ↓  /api/*
           nginx → FastAPI → PostgreSQL
              ↓
     Mistral (enrichment) · Grok/DuckDuckGo (discovery)
```

**Документация для разработки:** [`info/README.md`](info/README.md) — карта проекта, API, pipeline, файлы.

**Критические зависимости (не ломать):** [`info/CRITICAL-LINKS.md`](info/CRITICAL-LINKS.md)

Подробнее о pipeline: [`info/pipeline.md`](info/pipeline.md).

---

## Тесты

```bash
make test        # = cd backend && uv run pytest -v
```

Покрыто: CRUD эссе, SSE-fallback, фильтры слов/фраз, pipeline API и routing по теме.

## Миграции БД (Alembic)

Схема БД версионируется через Alembic (`backend/alembic/`). Миграции применяются
автоматически при `make up` (entrypoint контейнера делает `alembic upgrade head`).
После изменения моделей в `backend/app/db/models.py`:

```bash
make migration name="add xyz column"   # автогенерация из моделей
make migrate                           # применить к работающей БД
```
