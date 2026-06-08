# Спич на собеседование · Deutsch Essay Trainer (~10 минут)

> Формат: сначала общая картина, потом каждый блок с тремя уровнями глубины — **MVP** (обязательно сказать), **важно знать**, **плюс за погружение**.

---

## 0. Вступление (30 сек)

«Я сделал **Deutsch Essay Trainer** — full-stack прототип для подготовки к немецкому экзамену. Это не учебник и не чат-бот в вакууме: три связанные части — **тематический словарь**, **редактор эссе с AI-разбором** и **автономный pipeline**, который сам находит источники по теме, извлекает слова B2–C1 и записывает их в PostgreSQL. Backend на FastAPI, async SQLAlchemy, Docker. Репозиторий публичный, в README скриншоты и 16 pytest-тестов с CI на GitHub Actions.»

---

## 1. Продукт и зачем он нужен

### MVP — обязательно
- Проблема: готовясь к экзамену, нужны **тематический словарь**, **структура эссе** (Einleitung → Argumente → Schluss) и **обратная связь по языку**, а не только «переведи текст».
- Решение: одно приложение — словарь + редактор + автоматическое пополнение базы слов по теме.
- Целевой пользователь: изучающий немецкий на уровне B1–C1, пишущий argumentatives Essay.

### Важно знать
- UI — **прототип с продуманным дизайном** (watercolor-карточки, CEFR-уровни, русские подсказки в AI-разборе).
- Три страницы в проде: `index.html` (словарь), `editor.html` (редактор), `pipeline.html` (очередь тем).
- Данные живут в PostgreSQL; frontend ходит в API через nginx.

### Плюс за погружение
- Редактор заточен под **экзаменационный жанр**: клише по секциям эссе, словарь фильтруется по теме, прогресс 250 слов.
- AI-разбор даёт не только «исправь», а **B1- и B2-варианты** фразы + объяснение на русском — педагогический слой поверх LLM.
- Pipeline закрывает боль «откуда брать новые слова по теме Klimawandel / Migration» без ручного копипаста из статей.

---

## 2. Архитектура и стек

### MVP — обязательно
```
Браузер → nginx (статика + /api/*) → FastAPI → PostgreSQL
                              ↓
                    Mistral API · Grok API · Wiktionary
```
- **Три сервиса в docker-compose:** postgres, backend, frontend (nginx).
- **Слои backend:** `api/routes` → `services` / `pipeline` → `db/models`.
- **Стек:** Python 3.11, FastAPI, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, vanilla JS на фронте.

### Важно знать
- nginx проксирует `/api/*` на backend и отдаёт HTML/CSS/JS; отдельно проксируется `/health` для проверки живости API.
- Схема БД создаётся через `create_all` на старте + seed-данные (`init_data.py`) — осознанный MVP без Alembic.
- `editor-extract/` — **параллельный React+TipTap модуль**, не входит в Docker; в проде vanilla `editor.js` (~1500 строк).

### Плюс за погружение
- `JSON_TYPE = JSON().with_variant(JSONB, "postgresql")` — одна модель для SQLite в тестах и JSONB в проде.
- CORS настроен явно под локальный nginx (`8753`).
- Конфиг через `pydantic-settings` и `.env`: `MISTRAL_API_KEY`, `GROK_API_KEY`, `DATABASE_URL`.
- Паттерн **graceful degradation**: без ключей анализ эссе и pipeline не падают молча — есть fallback и явный `failed` статус.

---

## 3. Словарь (Wörterbuch)

### MVP — обязательно
- REST: `GET /api/words?topic=&level=&q=` — фильтры по теме, уровню CEFR, поиску.
- Карточка слова: немецкий, артикль, перевод, уровень, `grammar_data` (JSON), примеры.
- Связь слово ↔ тема через таблицу `word_topics` (many-to-many).

### Важно знать
- Часть слов — **seed** при первом старте (`ensure_seed_data`); часть приходит из **pipeline** (`source="pipeline"`).
- На фронте словарь рисует watercolor-подложки по формуле `уровень + род/тип слова` → файл из `worte/`.
- `POST /api/words/{id}/refresh-grammar` — подтягивание грамматики с de.wiktionary.org.

### Плюс за погружение
- `words_repo.py` — repository-слой, не SQL в роутерах.
- `grammar_parser.py` + `wiktionary_client.py` — нормализация сырого Wiktionary в структуру для UI.
- На главной `app.js` **мержит** статический дизайн-массив WORDS с API — UI не пустой до первого pipeline run.

---

## 4. Редактор эссе и AI-разбор

### MVP — обязательно
- Эссе из **4 секций**; текст собирается в один blob для backend с маркерами `Einleitung:`, `Argument Eins:` и т.д.
- CRUD: `POST/PATCH /api/essays`, автосохранение с debounce на фронте.
- **Главная фича:** `POST /api/essays/{id}/analyze/stream` — **SSE-стриминг** разбора по частям эссе.
- События: `part_start`, `part_done`, `done` — UI обновляется прогрессивно, не ждёт весь ответ.

### Важно знать
- Логика анализа в `mistral_analyzer.py` (~620 строк): промпты по частям, дедупликация ошибок, финальный summary.
- Ошибки привязываются к тексту: `excerpt`, `start`, `end`, тип (`grammar`, `vocabulary`, `style`).
- **Stale flag:** если текст изменили после анализа — `text_snapshot` не совпадает, анализ помечается устаревшим.
- Без `MISTRAL_API_KEY` — **fallback-режим** с демо-ошибками (тестируется в `test_stream_and_fallback.py`).

### Плюс за погружение
- На фронте `editor.js`: inline-аннотации (`span[data-annotation]`), popover с B1/B2 вариантами, re-anchor при редактировании (`reanchorSectionErrors`).
- `EditorApi.streamAnalyze()` парсит SSE-фреймы `data: {...}\n\n` через ReadableStream.
- `user_stats_service` пишет streak/статистику при анализе (hardcoded `user_id=1` — ограничение прототипа).
- Phrases API: `GET /api/phrases?part=einleitung&topic=technologie` — клише под секцию эссе.

---

## 5. Pipeline обогащения слов

### MVP — обязательно
- **Пять шагов** (см. `PIPELINE.md` и `runner.py`):
  1. **Discovery** — Grok API или DuckDuckGo fallback
  2. **Extraction** — скачивание статей + Mistral извлекает кандидатов-слов
  3. **Routing** — новые слова → на enrichment; существующие → только линк темы
  4. **Enrichment** — Wiktionary + DWDS + Mistral структурирует карточку
  5. **DB write** — upsert `Word` + `WordTopic`
- API: `POST /api/pipeline/run` → `BackgroundTasks` → polling `GET /api/pipeline/run/{id}`.
- UI `pipeline.html`: очередь тем, история запусков, статусы `running` / `completed` / `failed`.

### Важно знать
- Без `GROK_API_KEY` и без `article_urls` pipeline **явно падает** с ошибкой discovery — не висит бесконечно.
- Rate limits: семафоры `_WIKTIONARY_SEM = 5`, `_MISTRAL_SEM = 1` под free tier Mistral.
- Ошибки по стадиям в `errors_json` у `PipelineRun` — структура `PipelineError(stage, item, error)`.
- Параллельность: `asyncio.gather` на enrichment новых кандидатов.

### Плюс за погружение
- Discovery использует sync `requests` в `asyncio.to_thread` из-за TLS-особенностей — **задокументированный trade-off**, не «забыл async».
- Retry на HTTP 429 для Mistral в `enrichment.py` / `extraction.py`.
- `_route_words` обрабатывает `IntegrityError` при дубликате темы — unit-тест в `test_pipeline_runner.py`.
- Реальный успешный run на скриншоте: тема Klimawandel → **54 новых слова**.

---

## 6. Тестирование

### MVP — обязательно
- **16 pytest-тестов**, async mode, без реальных LLM-вызовов.
- `httpx.AsyncClient` + `ASGITransport(app)` — интеграционные тесты API in-process.
- `conftest.py`: override `get_db`, SQLite `test.db`, пустые API-ключи.
- Покрыто: CRUD эссе, SSE fallback, фильтры слов/фраз, **pipeline API** (start/poll/list), routing слов по теме.

### Важно знать
- Pipeline-тесты **мокают** `run_pipeline` в API-тестах — проверяют контракт, не внешние API.
- Отдельный тест: `run_pipeline` без Grok → статус `failed` + ошибка stage `fetch`.
- CI: GitHub Actions `.github/workflows/pytest.yml` на каждый push в `main`.

### Плюс за погружение
- Почему SQLite в тестах, Postgres в проде — скорость + `JSON().with_variant(JSONB)`; честно признаю, что JSONB-специфику не гоняю в CI.
- Что **не** покрыто: live Mistral, discovery scraping, frontend JS — осознанный scope для pet project.
- Как добавил бы: mocked `httpx` для Wiktionary, один integration test с `article_urls=[...]` и patch extraction.

---

## 7. Docker и демо на собесе

### MVP — обязательно
```bash
export MISTRAL_API_KEY=...
export GROK_API_KEY=...
docker compose up --build
```
- Словарь: http://localhost:8753
- Редактор: http://localhost:8753/editor.html
- Pipeline: http://localhost:8753/pipeline.html
- Swagger: http://localhost:8000/docs

### Важно знать
- Если редактор «пустой» (нет разделов/слов) — часто сломан bind-mount `js/` в контейнере; лечится `docker compose up -d --force-recreate frontend`.
- Скриншоты в `screenshots/` — то, что показывать, если live demo рискованна.

### Плюс за погружение
- postgres healthcheck в compose — backend стартует после готовности БД.
- nginx: статика с cache 7d, HTML без cache.
- Можно показать Network tab → SSE при «Analysieren».

---

## 8. Разработка с AI-агентами

### MVP — обязательно
- Проект активно разрабатывался с **Cursor** и agent-assisted workflow.
- Есть `.cursorrules`, подробный `PIPELINE.md`, extract-модуль как заготовка под рефакторинг.

### Важно знать
- Агент помогал с boilerplate FastAPI, pipeline orchestration, фронтовой интеграцией SSE.
- Архитектурные решения (семафоры, fallback, SSE) — осознанные, не «как сгенерировал».

### Плюс за погружение
- Пример промпта для pipeline описан в `PIPELINE.md`.
- Понимаю риски agent-generated code: дубли `editor-extract/`, расхождение доки и схемы — и как это чинить ревью + тестами.

---

## 9. Честные ограничения (если спросят)

### MVP — обязательно
- **Прототип**, не прод: нет auth, multi-user, rate limiting на API.
- Нет Alembic-миграций; dashboard/training в схемах, но не в API.
- Kafka/RabbitMQ нет — pipeline через `BackgroundTasks` + polling (достаточно для MVP).

### Важно знать
- Следующие шаги: Alembic, CI уже есть, auth JWT, убрать дубль `editor-extract/` или встроить в compose.
- Для стажировки в агентских backend-решениях этот проект близок по духу: **оркестратор → шаги → LLM tools → запись в БД**.

### Плюс за погружение
- Как бы перевёл на Kafka: discovery/enrichment как отдельные consumers, `PipelineRun` как saga state.
- Почему SSE, а не WebSocket: однонаправленный стрим от сервера, проще с HTTP/2 и nginx.

---

## 10. Закрытие (30 сек)

«Итого: я показал full-stack pet project с реальным async backend, LLM-оркестрацией и тестами. Сильнее всего — **pipeline обогащения слов** и **SSE-анализ эссе**; готов углубиться в код `runner.py`, `mistral_analyzer.py` или в тесты. Репозиторий на GitHub, скриншоты и спич — в `INTERVIEW_SPEECH.md`.»

---

## Шпаргалка: файлы «знать наизусть»

| Вопрос | Файл |
|--------|------|
| Точка входа API | `backend/app/main.py` |
| SSE-анализ эссе | `backend/app/services/mistral_analyzer.py` |
| Pipeline orchestration | `backend/app/pipeline/runner.py` |
| Pipeline API | `backend/app/api/routes/pipeline.py` |
| Модели БД | `backend/app/db/models.py` |
| Тесты pipeline | `backend/tests/test_pipeline_api.py` |
| Фронт редактора | `js/editor.js`, `js/editor-api.js` |
| Docker | `docker-compose.yml`, `nginx.conf` |
| Спека pipeline | `PIPELINE.md` |

---

## Тайминг (~10 мин)

| Блок | Минут |
|------|-------|
| Вступление | 0:30 |
| Продукт | 1:00 |
| Архитектура | 1:00 |
| Словарь | 1:00 |
| Редактор + AI | 2:00 |
| Pipeline | 2:30 |
| Тесты + CI | 1:00 |
| Docker / демо | 0:30 |
| AI-агенты | 0:30 |
| Ограничения + закрытие | 0:30 |
