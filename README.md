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

```bash
export MISTRAL_API_KEY=...   # enrichment + будущий AI-анализ
export GROK_API_KEY=...      # discovery в pipeline

docker compose up --build
```

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
cd backend && pip install -r requirements.txt && pytest -v
```

Покрыто: CRUD эссе, SSE-fallback, фильтры слов/фраз, pipeline API и routing по теме.
