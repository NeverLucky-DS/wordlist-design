# Deutsch Essay Trainer

**NLP / LLM** прототип для немецкого B1–C1: тематический словарь, streaming AI-разбор эссе, pipeline обогащения слов по теме.

**Репо:** https://github.com/NeverLucky-DS/wordlist-design

**Стек:** Mistral · Grok discovery · PostgreSQL · FastAPI · Docker · pytest (36)

## Демонстрация

### Редактор эссе

Структура из четырёх разделов, тематический словарь, клише по секциям, Pomodoro и AI-анализ текста.

![Редактор — карта эссе, клише и словарь по теме](screenshots/Deutsch_3.png)

![Редактор — набор текста с прогрессом и подсказками](screenshots/Deutsch_7.png)

![Редактор — карточка слова и связь со словарём](screenshots/Deutsch_1.png)

### AI-разбор текста

Streaming-анализ с подсветкой ошибок, объяснениями на русском и вариантами B1/B2.

![AI-аннотация с вариантами исправления](screenshots/Deutsch_8.png)

![Разбор аргумента с обратной связью и подсветкой](screenshots/Deutsch_9.png)

### Словарь (Wörterbuch)

Тематические фильтры, watercolor-карточки по уровню CEFR, детальная карточка с грамматикой и статистикой.

![Словарь — сетка карточек и распределение по уровням](screenshots/Deutsch_5.png)

![Словарь — детальная карточка слова](screenshots/Deutsch_4.png)

### Pipeline обогащения слов

Очередь тем: discovery → extraction → enrichment → запись в БД.

![Pipeline — очередь тем и история запусков](screenshots/Deutsch_6.png)

---

## Быстрый старт

```bash
export MISTRAL_API_KEY=...   # AI-анализ эссе
export GROK_API_KEY=...      # discovery в pipeline

docker compose up --build
```

| Страница | URL |
|----------|-----|
| Словарь | http://localhost:8753 |
| Редактор | http://localhost:8753/editor.html |
| Schreiben (roadmap) | http://localhost:8753/schreiben.html |
| Pipeline | http://localhost:8753/pipeline.html |
| API docs | http://localhost:8000/docs |

---

## Архитектура

```
index.html / editor.html / schreiben.html / pipeline.html
              ↓  /api/*
           nginx → FastAPI → PostgreSQL
              ↓
     Mistral (анализ, enrichment) · Grok/DuckDuckGo (discovery)
```

**Документация для разработки:** [`info/README.md`](info/README.md) — карта проекта, API, pipeline, файлы.

Подробнее о pipeline: [`PIPELINE.md`](PIPELINE.md) (длинный design doc; краткая версия — [`info/pipeline.md`](info/pipeline.md)).

---

## Тесты

```bash
cd backend && pip install -r requirements.txt && pytest -v
```

Покрыто: CRUD эссе, SSE-fallback, фильтры слов/фраз, pipeline API и routing по теме.
